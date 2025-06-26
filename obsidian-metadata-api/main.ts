import { Plugin, PluginSettingTab, Setting, App, TFile, Notice, TAbstractFile, EventRef } from 'obsidian';
import { MetadataAPISettings, DEFAULT_SETTINGS } from './src/settings';
import { SQLiteMetadataDB } from './src/database';

export default class MetadataAPIPlugin extends Plugin {
    settings: MetadataAPISettings;
    database: SQLiteMetadataDB;
    private eventRefs: EventRef[] = [];
    
    async onload() {
        await this.loadSettings();
        
        // Add settings tab
        this.addSettingTab(new MetadataAPISettingTab(this.app, this));
        
        // Initialize database
        const dbPath = this.getDbPath();
        this.database = new SQLiteMetadataDB(this.app, dbPath);
        await this.database.initDatabase();
        
        // Register event handlers
        this.registerEventHandlers();
        
        // Add commands
        this.addCommand({
            id: 'rebuild-metadata-database',
            name: 'Rebuild Metadata Database',
            callback: async () => {
                new Notice('Rebuilding metadata database...');
                await this.database.rebuildDatabase();
                new Notice('Metadata database rebuilt!');
            }
        });
        
        this.addCommand({
            id: 'show-database-path',
            name: 'Show Database Path',
            callback: () => {
                new Notice(`Database path: ${dbPath}`);
            }
        });
        
        // Initial database build
        setTimeout(async () => {
            await this.database.rebuildDatabase();
            new Notice('Metadata database initialized');
        }, 2000);
        
        // Plugin loaded
    }
    
    async onunload() {
        // Unregister all event handlers
        this.eventRefs.forEach(ref => this.app.vault.offref(ref));
        this.eventRefs = [];
        
        if (this.database) {
            await this.database.close();
        }
        
        // Plugin unloaded
    }
    
    getDbPath(): string {
        // Store database in plugin folder
        return this.app.vault.configDir + '/plugins/obsidian-metadata-api/metadata.json';
    }
    
    private registerEventHandlers() {
        // File created
        const createRef = this.app.vault.on('create', async (file: TAbstractFile) => {
            if (file instanceof TFile && file.extension === 'md') {
                // Wait a bit for metadata to be available
                setTimeout(async () => {
                    const metadata = this.app.metadataCache.getFileCache(file);
                    await this.database.updateNote(file, metadata);
                }, 1000);
            }
        });
        this.eventRefs.push(createRef);
        
        // File modified
        const modifyRef = this.app.vault.on('modify', async (file: TAbstractFile) => {
            if (file instanceof TFile && file.extension === 'md') {
                const metadata = this.app.metadataCache.getFileCache(file);
                await this.database.updateNote(file, metadata);
            }
        });
        this.eventRefs.push(modifyRef);
        
        // File deleted
        const deleteRef = this.app.vault.on('delete', async (file: TAbstractFile) => {
            if (file instanceof TFile && file.extension === 'md') {
                await this.database.deleteNote(file.path);
            }
        });
        this.eventRefs.push(deleteRef);
        
        // File renamed
        const renameRef = this.app.vault.on('rename', async (file: TAbstractFile, oldPath: string) => {
            if (file instanceof TFile && file.extension === 'md') {
                await this.database.deleteNote(oldPath);
                const metadata = this.app.metadataCache.getFileCache(file);
                await this.database.updateNote(file, metadata);
            }
        });
        this.eventRefs.push(renameRef);
        
        // Metadata cache changed - this catches tag updates, link updates, etc.
        const metadataRef = this.app.metadataCache.on('changed', async (file: TFile) => {
            if (file.extension === 'md') {
                const metadata = this.app.metadataCache.getFileCache(file);
                await this.database.updateNote(file, metadata);
            }
        });
        this.eventRefs.push(metadataRef);
    }
    
    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }
    
    async saveSettings() {
        await this.saveData(this.settings);
    }
}

class MetadataAPISettingTab extends PluginSettingTab {
    plugin: MetadataAPIPlugin;
    
    constructor(app: App, plugin: MetadataAPIPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }
    
    display(): void {
        const { containerEl } = this;
        
        containerEl.empty();
        
        containerEl.createEl('h2', { text: 'Metadata API Settings' });
        
        new Setting(containerEl)
            .setName('Database Path')
            .setDesc('Path where the metadata database is stored')
            .addText(text => text
                .setValue(this.plugin.getDbPath())
                .setDisabled(true));
        
        new Setting(containerEl)
            .setName('Auto-update')
            .setDesc('Automatically update database when files change')
            .addToggle(toggle => toggle
                .setValue(true)
                .setDisabled(true));
        
        new Setting(containerEl)
            .setName('Rebuild Database')
            .setDesc('Rebuild the entire metadata database from scratch')
            .addButton(button => button
                .setButtonText('Rebuild')
                .onClick(async () => {
                    new Notice('Rebuilding metadata database...');
                    await this.plugin.database.rebuildDatabase();
                    new Notice('Database rebuilt!');
                }));
        
        containerEl.createEl('h3', { text: 'Database Info' });
        
        // Show database stats
        this.showDatabaseStats(containerEl);
    }
    
    private async showDatabaseStats(containerEl: HTMLElement) {
        try {
            const dbPath = this.plugin.getDbPath();
            const content = await this.plugin.app.vault.adapter.read(dbPath);
            const db = JSON.parse(content);
            
            const statsEl = containerEl.createEl('div', { cls: 'metadata-api-stats' });
            statsEl.createEl('p', { text: `Total Notes: ${db.stats.totalNotes}` });
            statsEl.createEl('p', { text: `Total Tags: ${db.stats.totalTags}` });
            statsEl.createEl('p', { text: `Total Links: ${db.stats.totalLinks}` });
            statsEl.createEl('p', { text: `Last Updated: ${new Date(db.stats.lastUpdated).toLocaleString()}` });
        } catch (e) {
            containerEl.createEl('p', { text: 'Database not yet initialized' });
        }
    }
}