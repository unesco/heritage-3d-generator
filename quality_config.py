#!/usr/bin/env python3
"""
🎯 UNESCO Heritage Sites Quality Configuration System
Defines render quality presets for different use cases

Quality Levels:
- PREVIEW: Fast preview (large voxels, basic sources)  
- STANDARD: Balanced quality/speed (current settings)
- PREMIUM: High quality (fine detail, best sources)
- ULTIMATE: Maximum quality (finest detail, all sources)
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

@dataclass
class QualityConfig:
    """Configuration for a specific render quality level"""
    name: str
    description: str
    zone_size: int  # Coverage area in meters
    mesh_size: int  # Voxel resolution in meters
    building_source: str
    land_cover_source: str
    canopy_height_source: str
    dem_source: str
    dem_interpolation: bool
    estimated_time: str  # Estimated processing time
    voxel_count: int  # Total number of voxels
    use_case: str  # When to use this preset
    
    @property
    def coverage_km2(self) -> float:
        """Coverage area in square kilometers"""
        return (self.zone_size / 1000) ** 2
    
    @property
    def detail_level(self) -> str:
        """Human readable detail level"""
        if self.mesh_size >= 10:
            return "Low Detail"
        elif self.mesh_size >= 5:
            return "Medium Detail" 
        elif self.mesh_size >= 2:
            return "High Detail"
        else:
            return "Ultra Detail"

class QualityManager:
    """Manages different quality presets for UNESCO heritage site rendering"""
    
    def __init__(self):
        self.presets = self._define_presets()
        
    def _define_presets(self) -> Dict[str, QualityConfig]:
        """Define all quality presets"""
        
        # PREVIEW: Quick testing and exploration
        preview = QualityConfig(
            name="PREVIEW",
            description="🚀 Fast preview for testing locations",
            zone_size=500,  # 0.25 km²
            mesh_size=10,   # 10m voxels
            building_source="OpenStreetMap",
            land_cover_source="OpenStreetMap", 
            canopy_height_source="ETH Global Sentinel-2 10m",
            dem_source="FABDEM",
            dem_interpolation=False,
            estimated_time="30-60 seconds",
            voxel_count=2500,  # 50x50 grid
            use_case="Quick location testing, initial exploration"
        )
        
        # STANDARD: Balanced (current settings)
        standard = QualityConfig(
            name="STANDARD", 
            description="⚖️ Balanced quality and speed",
            zone_size=750,  # 0.56 km²
            mesh_size=5,    # 5m voxels
            building_source="OpenStreetMap",
            land_cover_source="OpenStreetMap",
            canopy_height_source="ETH Global Sentinel-2 10m",
            dem_source="FABDEM", 
            dem_interpolation=True,
            estimated_time="2-4 minutes",
            voxel_count=22500,  # 150x150 grid
            use_case="General UNESCO documentation, presentations"
        )
        
        # PREMIUM: High quality for important sites
        premium = QualityConfig(
            name="PREMIUM",
            description="🏆 High quality for key heritage sites", 
            zone_size=1000,  # 1.0 km²
            mesh_size=3,     # 3m voxels
            building_source="OpenStreetMap",
            land_cover_source="OpenStreetMap",  # Reliable OSM
            canopy_height_source="ETH Global Sentinel-2 10m Canopy Height (2020)",  # Reliable ETH data
            dem_source="FABDEM",
            dem_interpolation=True,
            estimated_time="8-15 minutes",
            voxel_count=111111,  # 333x333 grid
            use_case="Important heritage site documentation, research"
        )
        
        # ULTIMATE: Maximum quality for critical documentation
        ultimate = QualityConfig(
            name="ULTIMATE",
            description="💎 Maximum quality for critical documentation",
            zone_size=1200,  # 1.44 km² 
            mesh_size=2,     # 2m voxels
            building_source="OpenStreetMap",  # Reliable OSM
            land_cover_source="OpenStreetMap",  # Reliable OSM
            canopy_height_source="ETH Global Sentinel-2 10m Canopy Height (2020)",  # Reliable ETH data
            dem_source="FABDEM",  # Reliable FABDEM
            dem_interpolation=True,
            estimated_time="20-45 minutes",
            voxel_count=360000,  # 600x600 grid
            use_case="Critical heritage preservation, academic research"
        )
        
        return {
            "preview": preview,
            "standard": standard, 
            "premium": premium,
            "ultimate": ultimate
        }
    
    def get_preset(self, quality: str) -> QualityConfig:
        """Get a quality preset by name"""
        quality_lower = quality.lower()
        if quality_lower in self.presets:
            return self.presets[quality_lower]
        else:
            available = list(self.presets.keys())
            raise ValueError(f"Quality '{quality}' not found. Available: {available}")
    
    def list_presets(self) -> None:
        """Display all available quality presets"""
        table = Table(title="🎯 UNESCO Heritage Sites Quality Presets")
        table.add_column("Quality", style="bold cyan", no_wrap=True)
        table.add_column("Coverage", style="green")
        table.add_column("Detail", style="yellow") 
        table.add_column("Time", style="magenta")
        table.add_column("Voxels", style="blue")
        table.add_column("Use Case", style="dim")
        
        for preset in self.presets.values():
            table.add_row(
                f"{preset.name}",
                f"{preset.zone_size}m × {preset.zone_size}m\n({preset.coverage_km2:.2f} km²)",
                f"{preset.mesh_size}m voxels\n{preset.detail_level}",
                preset.estimated_time,
                f"{preset.voxel_count:,}",
                preset.use_case
            )
        
        console.print(table)
    
    def show_preset_details(self, quality: str) -> None:
        """Show detailed information about a specific preset"""
        preset = self.get_preset(quality)
        
        # Create info panel
        info_text = Text()
        info_text.append(f"{preset.description}\n\n", style="bold")
        info_text.append("📐 Spatial Configuration:\n", style="bold cyan")
        info_text.append(f"• Zone Size: {preset.zone_size}m × {preset.zone_size}m ({preset.coverage_km2:.2f} km²)\n")
        info_text.append(f"• Resolution: {preset.mesh_size}m voxels ({preset.detail_level})\n")
        info_text.append(f"• Total Voxels: {preset.voxel_count:,}\n\n")
        
        info_text.append("🗂️ Data Sources:\n", style="bold green")
        info_text.append(f"• Buildings: {preset.building_source}\n")
        info_text.append(f"• Land Cover: {preset.land_cover_source}\n") 
        info_text.append(f"• Canopy: {preset.canopy_height_source}\n")
        info_text.append(f"• Terrain: {preset.dem_source}\n")
        info_text.append(f"• DEM Interpolation: {'✅' if preset.dem_interpolation else '❌'}\n\n")
        
        info_text.append("⏱️ Performance:\n", style="bold yellow")
        info_text.append(f"• Estimated Time: {preset.estimated_time}\n")
        info_text.append(f"• Best For: {preset.use_case}")
        
        panel = Panel(
            info_text,
            title=f"[bold white]{preset.name} Quality Preset[/bold white]",
            border_style="blue"
        )
        console.print(panel)
    
    def apply_preset_to_env(self, quality: str, env_file: str = ".env") -> None:
        """Apply a quality preset to the .env file"""
        preset = self.get_preset(quality)
        
        # Read current .env file
        env_path = Path(env_file)
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add preset values
        updates = {
            'ZONE_SIZE_METERS': str(preset.zone_size),
            'MESH_SIZE_METERS': str(preset.mesh_size),
            'BUILDING_SOURCE': preset.building_source,
            'LAND_COVER_SOURCE': preset.land_cover_source,
            'CANOPY_HEIGHT_SOURCE': preset.canopy_height_source,
            'DEM_SOURCE': preset.dem_source,
            'DEM_INTERPOLATION': str(preset.dem_interpolation).lower()
        }
        
        # Process each line
        new_lines = []
        updated_keys = set()
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                key = line.split('=')[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line + '\n')
            else:
                new_lines.append(line + '\n')
        
        # Add any missing keys
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}\n")
        
        # Add quality preset comment
        new_lines.insert(0, f"# Quality Preset: {preset.name} - {preset.description}\n")
        new_lines.insert(1, f"# Applied on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        console.print(f"[green]✅ Applied {preset.name} quality preset to {env_file}[/green]")
        self.show_preset_details(quality)
    
    def get_preset_kwargs(self, quality: str) -> Dict[str, Any]:
        """Get kwargs dictionary for VoxCity from a preset"""
        preset = self.get_preset(quality)
        
        return {
            "output_dir": os.getenv('OUTPUT_DIR', 'output'),
            "dem_interpolation": preset.dem_interpolation
        }

# Convenience functions for easy usage
def get_quality_manager() -> QualityManager:
    """Get a QualityManager instance"""
    return QualityManager()

def list_quality_presets() -> None:
    """List all available quality presets"""
    manager = get_quality_manager()
    manager.list_presets()

def apply_quality_preset(quality: str, env_file: str = ".env") -> None:
    """Apply a quality preset to .env file"""
    manager = get_quality_manager()
    manager.apply_preset_to_env(quality, env_file)

def show_quality_details(quality: str) -> None:
    """Show details for a specific quality preset"""
    manager = get_quality_manager()
    manager.show_preset_details(quality)

def get_quality_config(quality: str) -> QualityConfig:
    """Get quality configuration object"""
    manager = get_quality_manager()
    return manager.get_preset(quality)

# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    manager = get_quality_manager()
    
    if len(sys.argv) == 1:
        # Show all presets
        manager.list_presets()
        console.print("\n[bold cyan]Usage:[/bold cyan]")
        console.print("python quality_config.py [preset_name]     # Show preset details")
        console.print("python quality_config.py apply [preset]    # Apply preset to .env")
        
    elif len(sys.argv) == 2:
        # Show specific preset
        try:
            manager.show_preset_details(sys.argv[1])
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")
            
    elif len(sys.argv) == 3 and sys.argv[1] == "apply":
        # Apply preset
        try:
            manager.apply_preset_to_env(sys.argv[2])
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")
    
    else:
        console.print("[red]❌ Invalid arguments[/red]")
