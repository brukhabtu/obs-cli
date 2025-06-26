import { App, TFile, TAbstractFile, CachedMetadata } from 'obsidian';

export interface MetadataDB {
    path: string;
    initDatabase(): Promise<void>;
    updateNote(file: TFile, metadata: CachedMetadata | null): Promise<void>;
    deleteNote(path: string): Promise<void>;
    updateTags(): Promise<void>;
    close(): Promise<void>;
}

export class SQLiteMetadataDB implements MetadataDB {
    path: string;
    private db: any;
    private app: App;
    
    constructor(app: App, dbPath: string) {
        this.app = app;
        this.path = dbPath;
    }
    
    async initDatabase(): Promise<void> {
        // For mobile, we'll write to JSON files instead of SQLite
        // This avoids needing native modules
        await this.ensureDataDirectory();
        await this.initializeJsonDb();
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
            notes: {},
            tags: {},
            links: {},
            folders: {},
            stats: {
                totalNotes: 0,
                totalTags: 0,
                totalLinks: 0,
                totalEmbeds: 0,
                totalTasks: 0,
                totalIncompleteTasks: 0,
                lastUpdated: new Date().toISOString()
            }
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
    
    async updateNote(file: TFile, metadata: CachedMetadata | null): Promise<void> {
        const db = await this.readDb();
        
        // Read file content once for tasks and code blocks
        let content: string | null = null;
        let lines: string[] | null = null;
        
        if (metadata?.listItems || metadata?.sections) {
            content = await this.app.vault.read(file);
            lines = content.split('\n');
        }
        
        // Extract tags
        const tags: string[] = [];
        if (metadata?.tags) {
            metadata.tags.forEach(tag => {
                tags.push(tag.tag.substring(1)); // Remove #
            });
        }
        if (metadata?.frontmatter?.tags) {
            const fmTags = metadata.frontmatter.tags;
            if (Array.isArray(fmTags)) {
                tags.push(...fmTags);
            } else if (typeof fmTags === 'string') {
                tags.push(fmTags);
            }
        }
        
        // Extract links
        const outlinks: string[] = [];
        if (metadata?.links) {
            metadata.links.forEach(link => {
                const linkedFile = this.app.metadataCache.getFirstLinkpathDest(link.link, file.path);
                if (linkedFile) {
                    outlinks.push(linkedFile.path);
                }
            });
        }
        
        // Extract embeds
        const embeds: string[] = [];
        if (metadata?.embeds) {
            metadata.embeds.forEach(embed => {
                const embeddedFile = this.app.metadataCache.getFirstLinkpathDest(embed.link, file.path);
                if (embeddedFile) {
                    embeds.push(embeddedFile.path);
                }
            });
        }
        
        // Extract tasks
        const tasks: Array<{ text: string, completed: boolean, line: number }> = [];
        if (metadata?.listItems && lines) {
            metadata.listItems.forEach(item => {
                // Check if this is a task item (has task property)
                if (item.task !== undefined) {
                    const lineText = lines![item.position.start.line] || '';
                    // Extract text after the checkbox pattern (- [ ] or - [x])
                    const taskMatch = lineText.match(/^[\s\t]*-\s*\[[^\]]\]\s*(.*)$/);
                    const taskText = taskMatch ? taskMatch[1].trim() : lineText.trim();
                    
                    tasks.push({
                        text: taskText,
                        completed: item.task !== ' ', // Space means incomplete
                        line: item.position.start.line + 1 // 1-based for display
                    });
                }
            });
        }
        
        // Extract code blocks
        const codeBlocks: Array<{ language: string, count: number }> = [];
        if (metadata?.sections && lines) {
            const languageCounts: Record<string, number> = {};
            
            metadata.sections.forEach(section => {
                if (section.type === 'code') {
                    // Try to extract language from the opening code fence
                    const startLine = lines![section.position.start.line] || '';
                    const langMatch = startLine.match(/^```(\w+)/);
                    const language = langMatch ? langMatch[1].toLowerCase() : 'unknown';
                    languageCounts[language] = (languageCounts[language] || 0) + 1;
                }
            });
            
            // Convert counts to array format
            for (const [language, count] of Object.entries(languageCounts)) {
                codeBlocks.push({ language, count });
            }
        }
        
        // Update note entry
        db.notes[file.path] = {
            path: file.path,
            basename: file.basename,
            extension: file.extension,
            size: file.stat.size,
            ctime: file.stat.ctime,
            mtime: file.stat.mtime,
            tags: [...new Set(tags)], // Remove duplicates
            outlinks,
            embeds,
            frontmatter: metadata?.frontmatter || {},
            headings: metadata?.headings?.map(h => ({
                level: h.level,
                text: h.heading
            })) || [],
            tasks,
            codeBlocks,
            folder: file.parent?.path || ''
        };
        
        // Update stats
        db.stats.totalNotes = Object.keys(db.notes).length;
        db.stats.lastUpdated = new Date().toISOString();
        
        await this.writeDb(db);
        await this.updateTags();
    }
    
    async deleteNote(path: string): Promise<void> {
        const db = await this.readDb();
        delete db.notes[path];
        
        // Update stats
        db.stats.totalNotes = Object.keys(db.notes).length;
        db.stats.lastUpdated = new Date().toISOString();
        
        await this.writeDb(db);
        await this.updateTags();
    }
    
    async updateTags(): Promise<void> {
        const db = await this.readDb();
        const tagCounts: Record<string, number> = {};
        const folderCounts: Record<string, number> = {};
        
        // Count tags across all notes
        Object.values(db.notes).forEach((note: any) => {
            note.tags.forEach((tag: string) => {
                tagCounts[tag] = (tagCounts[tag] || 0) + 1;
            });
            
            // Count notes per folder
            const folder = note.folder || 'root';
            folderCounts[folder] = (folderCounts[folder] || 0) + 1;
        });
        
        db.tags = tagCounts;
        db.folders = folderCounts;
        db.stats.totalTags = Object.keys(tagCounts).length;
        
        // Update links/backlinks
        const links: Record<string, { outlinks: string[], backlinks: string[] }> = {};
        
        Object.values(db.notes).forEach((note: any) => {
            if (!links[note.path]) {
                links[note.path] = { outlinks: [], backlinks: [] };
            }
            links[note.path].outlinks = note.outlinks;
            
            // Add backlinks
            note.outlinks.forEach((targetPath: string) => {
                if (!links[targetPath]) {
                    links[targetPath] = { outlinks: [], backlinks: [] };
                }
                if (!links[targetPath].backlinks.includes(note.path)) {
                    links[targetPath].backlinks.push(note.path);
                }
            });
        });
        
        db.links = links;
        db.stats.totalLinks = Object.values(db.notes).reduce((sum: number, note: any) => 
            sum + note.outlinks.length, 0);
        db.stats.totalEmbeds = Object.values(db.notes).reduce((sum: number, note: any) => 
            sum + note.embeds.length, 0);
        
        // Update task stats
        let totalTasks = 0;
        let totalIncompleteTasks = 0;
        Object.values(db.notes).forEach((note: any) => {
            if (note.tasks) {
                totalTasks += note.tasks.length;
                totalIncompleteTasks += note.tasks.filter((task: any) => !task.completed).length;
            }
        });
        db.stats.totalTasks = totalTasks;
        db.stats.totalIncompleteTasks = totalIncompleteTasks;
        
        await this.writeDb(db);
    }
    
    async rebuildDatabase(): Promise<void> {
        // Rebuilding metadata database
        
        // Clear existing data
        const db = {
            notes: {},
            tags: {},
            links: {},
            folders: {},
            stats: {
                totalNotes: 0,
                totalTags: 0,
                totalLinks: 0,
                totalEmbeds: 0,
                totalTasks: 0,
                totalIncompleteTasks: 0,
                lastUpdated: new Date().toISOString()
            }
        };
        await this.writeDb(db);
        
        // Process all markdown files
        const files = this.app.vault.getMarkdownFiles();
        for (const file of files) {
            const metadata = this.app.metadataCache.getFileCache(file);
            await this.updateNote(file, metadata);
        }
        
        // Database rebuilt
    }
    
    async close(): Promise<void> {
        // Nothing to close for JSON implementation
    }
}