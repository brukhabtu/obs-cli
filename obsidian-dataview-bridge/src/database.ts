import { App, Plugin } from 'obsidian';

export interface DataviewBridge {
    path: string;
    initDatabase(): Promise<void>;
    close(): Promise<void>;
}

export class DataviewQueryBridge implements DataviewBridge {
    path: string;
    private app: App;
    private queryCheckInterval: number | null = null;
    
    constructor(app: App, dbPath: string) {
        this.app = app;
        this.path = dbPath;
    }
    
    async initDatabase(): Promise<void> {
        await this.ensureDataDirectory();
        await this.initializeJsonDb();
        
        // Start checking for Dataview queries
        this.startDataviewQueryChecker();
    }
    
    private async ensureDataDirectory(): Promise<void> {
        const dataDir = this.path.substring(0, this.path.lastIndexOf('/'));
        try {
            await this.app.vault.adapter.mkdir(dataDir);
        } catch (e) {
            // Directory might already exist
        }
    }
    
    private async initializeJsonDb(): Promise<void> {
        const defaultData = {
            version: '2.0.0',
            dataviewAvailable: false,
            dataviewQueries: {},
            lastChecked: new Date().toISOString()
        };
        
        try {
            await this.app.vault.adapter.read(this.path);
        } catch (e) {
            // File doesn't exist, create it
            await this.app.vault.adapter.write(this.path, JSON.stringify(defaultData, null, 2));
        }
    }
    
    private async readDb(): Promise<any> {
        const content = await this.app.vault.adapter.read(this.path);
        return JSON.parse(content);
    }
    
    private async writeDb(data: any): Promise<void> {
        await this.app.vault.adapter.write(this.path, JSON.stringify(data, null, 2));
    }
    
    async close(): Promise<void> {
        // Stop query checker
        if (this.queryCheckInterval !== null) {
            window.clearInterval(this.queryCheckInterval);
            this.queryCheckInterval = null;
        }
    }
    
    private startDataviewQueryChecker(): void {
        // Check every 500ms for pending queries
        this.queryCheckInterval = window.setInterval(async () => {
            await this.checkAndExecuteDataviewQueries();
        }, 500);
        
        // Also do an initial availability check after a delay
        setTimeout(async () => {
            await this.checkDataviewAvailability();
        }, 2000);
        
        // Also check Dataview availability immediately
        this.checkDataviewAvailability();
    }
    
    async checkDataviewAvailability(): Promise<void> {
        const db = await this.readDb();
        
        // Check if Dataview plugin is available and enabled
        const dataviewPlugin = (this.app as any).plugins?.plugins?.dataview;
        const isAvailable = !!(dataviewPlugin && dataviewPlugin.api);
        
        db.dataviewAvailable = isAvailable;
        db.lastChecked = new Date().toISOString();
        await this.writeDb(db);
    }
    
    private async checkAndExecuteDataviewQueries(): Promise<void> {
        const db = await this.readDb();
        
        if (!db.dataviewQueries) {
            return;
        }
        
        // Check for Dataview availability check request
        if (db.dataviewQueries._check && db.dataviewQueries._check.status === 'pending') {
            await this.checkDataviewAvailability();
            delete db.dataviewQueries._check;
            await this.writeDb(db);
            return;
        }
        
        // Look for pending queries
        const pendingQueries = Object.entries(db.dataviewQueries).filter(
            ([id, query]: [string, any]) => !id.startsWith('_') && query.status === 'pending'
        );
        
        if (pendingQueries.length === 0) {
            return;
        }
        
        // Get Dataview API
        const dataviewPlugin = (this.app as any).plugins?.plugins?.dataview;
        if (!dataviewPlugin || !dataviewPlugin.api) {
            // Mark queries as failed
            for (const [queryId, queryData] of pendingQueries) {
                db.dataviewQueries[queryId] = {
                    ...queryData as any,
                    status: 'error',
                    error: 'Dataview plugin not available',
                    timestamp: new Date().toISOString()
                };
            }
            await this.writeDb(db);
            return;
        }
        
        const dv = dataviewPlugin.api;
        
        // Execute each pending query
        for (const [queryId, queryData] of pendingQueries) {
            const query = (queryData as any).query;
            
            try {
                // Use Dataview's query API
                const result = await dv.query(query);
                
                if (result.successful) {
                    // Store the raw result - data is in result.value
                    const queryResult = result.value;
                    db.dataviewQueries[queryId] = {
                        query: query,
                        status: 'success',
                        result: {
                            type: queryResult.type,
                            headers: queryResult.headers || [],
                            values: queryResult.values || [],
                            // Store additional metadata if available
                            ...(queryResult.type === 'table' && {
                                columnTypes: queryResult.columnTypes || []
                            })
                        },
                        timestamp: new Date().toISOString()
                    };
                } else {
                    throw new Error(result.error || 'Query failed');
                }
                
            } catch (error: any) {
                // Update with error
                db.dataviewQueries[queryId] = {
                    query: query,
                    status: 'error',
                    error: error.message || 'Query execution failed',
                    timestamp: new Date().toISOString()
                };
            }
        }
        
        // Clean up old queries (older than 24 hours)
        const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
        Object.entries(db.dataviewQueries).forEach(([id, query]: [string, any]) => {
            if (!id.startsWith('_') && query.timestamp && query.timestamp < oneDayAgo) {
                delete db.dataviewQueries[id];
            }
        });
        
        await this.writeDb(db);
    }
}