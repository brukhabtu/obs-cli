import { Plugin, PluginSettingTab, Setting, App, Notice } from 'obsidian';
import { MetadataAPISettings, DEFAULT_SETTINGS } from './src/settings';
import { DataviewQueryBridge } from './src/database';

export default class DataviewBridgePlugin extends Plugin {
    settings: MetadataAPISettings;
    database: DataviewQueryBridge;
    
    async onload() {
        await this.loadSettings();
        
        // Add settings tab
        this.addSettingTab(new DataviewBridgeSettingTab(this.app, this));
        
        // Initialize database
        const dbPath = this.getDbPath();
        this.database = new DataviewQueryBridge(this.app, dbPath);
        await this.database.initDatabase();
        
        // Wait for workspace to be ready before checking for Dataview
        this.app.workspace.onLayoutReady(() => {
            // Check for Dataview when layout is ready
            this.database.checkDataviewAvailability();
            
            // Also listen for dataview to be ready
            this.registerEvent(
                this.app.metadataCache.on('dataview:index-ready' as any, () => {
                    console.log('Dataview index ready!');
                    this.database.checkDataviewAvailability();
                })
            );
        });
        
        // Add commands
        this.addCommand({
            id: 'check-dataview-status',
            name: 'Check Dataview Status',
            callback: async () => {
                const dv = (this.app as any).plugins?.plugins?.dataview;
                if (dv) {
                    new Notice(`Dataview found! API available: ${!!dv.api}`);
                    console.log('Dataview plugin:', dv);
                    console.log('Dataview API:', dv.api);
                } else {
                    new Notice('Dataview not found');
                }
            }
        });
        
        this.addCommand({
            id: 'show-bridge-path',
            name: 'Show Bridge Database Path',
            callback: () => {
                new Notice(`Bridge database path: ${dbPath}`);
            }
        });
        
        // Plugin loaded
        new Notice('Dataview Bridge initialized');
    }
    
    async onunload() {
        if (this.database) {
            await this.database.close();
        }
        
        // Plugin unloaded
    }
    
    getDbPath(): string {
        // Store database in plugin folder
        return this.app.vault.configDir + '/plugins/obsidian-metadata-api/metadata.json';
    }
    
    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }
    
    async saveSettings() {
        await this.saveData(this.settings);
    }
}

class DataviewBridgeSettingTab extends PluginSettingTab {
    plugin: DataviewBridgePlugin;
    
    constructor(app: App, plugin: DataviewBridgePlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }
    
    display(): void {
        const { containerEl } = this;
        
        containerEl.empty();
        
        containerEl.createEl('h2', { text: 'Dataview Bridge Settings' });
        
        new Setting(containerEl)
            .setName('Bridge Database Path')
            .setDesc('Path where the bridge database is stored')
            .addText(text => text
                .setValue(this.plugin.getDbPath())
                .setDisabled(true));
        
        new Setting(containerEl)
            .setName('Check Dataview Status')
            .setDesc('Check if Dataview plugin is available and ready')
            .addButton(button => button
                .setButtonText('Check Status')
                .onClick(async () => {
                    await this.plugin.database.checkDataviewAvailability();
                    const dv = (this.plugin.app as any).plugins?.plugins?.dataview;
                    if (dv && dv.api) {
                        new Notice('Dataview is available and ready!');
                    } else {
                        new Notice('Dataview is not available');
                    }
                }));
        
        containerEl.createEl('h3', { text: 'Bridge Info' });
        
        // Show bridge stats
        this.showBridgeStats(containerEl);
    }
    
    private async showBridgeStats(containerEl: HTMLElement) {
        try {
            const dbPath = this.plugin.getDbPath();
            const content = await this.plugin.app.vault.adapter.read(dbPath);
            const db = JSON.parse(content);
            
            const statsEl = containerEl.createEl('div', { cls: 'dataview-bridge-stats' });
            statsEl.createEl('p', { text: `Dataview Available: ${db.dataviewAvailable ? 'Yes' : 'No'}` });
            statsEl.createEl('p', { text: `Last Checked: ${new Date(db.lastChecked).toLocaleString()}` });
            
            const queryCount = Object.keys(db.dataviewQueries || {}).filter(k => !k.startsWith('_')).length;
            statsEl.createEl('p', { text: `Cached Queries: ${queryCount}` });
        } catch (e) {
            containerEl.createEl('p', { text: 'Bridge database not yet initialized' });
        }
    }
}