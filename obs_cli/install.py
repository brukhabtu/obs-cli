"""Plugin installation functionality for Obsidian vaults."""

import shutil
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


def install_plugin(vault_path: str) -> bool:
    """
    Install the Obsidian Dataview Bridge plugin to the specified vault.
    
    Args:
        vault_path: Path to the Obsidian vault
        
    Returns:
        True if installation succeeded, False otherwise
    """
    try:
        vault = Path(vault_path).expanduser().resolve()
        
        if not vault.exists():
            console.print(f"[red]Error:[/red] Vault path does not exist: {vault}")
            return False
            
        if not vault.is_dir():
            console.print(f"[red]Error:[/red] Vault path is not a directory: {vault}")
            return False
        
        # Find the plugin files relative to this script
        current_dir = Path(__file__).parent.parent
        plugin_dir = current_dir / "obsidian-dataview-bridge"
        
        if not plugin_dir.exists():
            console.print(f"[red]Error:[/red] Plugin directory not found: {plugin_dir}")
            return False
        
        # Build the plugin first
        console.print("[yellow]Building plugin...[/yellow]")
        import subprocess
        try:
            result = subprocess.run(
                ["npm", "run", "build"], 
                cwd=plugin_dir, 
                capture_output=True, 
                text=True, 
                check=True
            )
            console.print("[green]Plugin built successfully![/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error:[/red] Failed to build plugin: {e.stderr}")
            return False
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] npm not found. Please install Node.js and npm")
            return False
        
        # Check if plugin files exist
        main_js = plugin_dir / "main.js"
        manifest_json = plugin_dir / "manifest.json"
        
        if not main_js.exists():
            console.print(f"[red]Error:[/red] Plugin build failed - main.js not found")
            return False
            
        if not manifest_json.exists():
            console.print(f"[red]Error:[/red] Missing manifest.json in {plugin_dir}")
            return False
        
        # Create plugin directory in vault (remove existing first)
        plugin_name = "obsidian-dataview-bridge"
        vault_plugin_dir = vault / ".obsidian" / "plugins" / plugin_name
        
        # Remove existing plugin directory
        shutil.rmtree(vault_plugin_dir, ignore_errors=True)
        vault_plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy plugin files
        shutil.copy2(main_js, vault_plugin_dir / "main.js")
        shutil.copy2(manifest_json, vault_plugin_dir / "manifest.json")
        
        console.print(f"[green]Success![/green] Plugin installed to: {vault_plugin_dir}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("1. Open Obsidian")
        console.print("2. Go to Settings → Community plugins")
        console.print("3. Enable 'Obsidian Dataview Bridge'")
        console.print("4. The plugin will start monitoring your vault and create the metadata database")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to install plugin: {str(e)}")
        return False