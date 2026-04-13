#!/usr/bin/env python3
"""
🏛️ UNESCO Heritage Sites 3D Generator with Quality Presets
Enhanced main script with configurable quality levels

Usage: 
    python main.py                                    # Interactive mode
    python main.py test                               # Mont-Saint-Michel test  
    python main.py <site_number>                      # Process specific heritage site
    python main.py <site_number> --quality <preset>  # Use specific quality preset
    python main.py --quality <preset>                # Interactive with quality preset
    python main.py --list-quality                    # List available quality presets
    python main.py --quality-details <preset>        # Show quality preset details
"""

import sys
import os
import warnings
import pandas as pd
import ee
import argparse
from dotenv import load_dotenv
from pathlib import Path
from math import cos, radians
from typing import Tuple, Optional, List
import time

# Rich imports for beautiful console output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from rich.prompt import Prompt, IntPrompt, Confirm

# Tenacity for robust API calls
from tenacity import retry, stop_after_attempt, wait_exponential

# Quality system import
try:
    from quality_config import QualityManager, get_quality_manager
    QUALITY_SYSTEM_AVAILABLE = True
except ImportError:
    QUALITY_SYSTEM_AVAILABLE = False

# Suppress warnings
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')
warnings.filterwarnings('ignore', category=UserWarning, module='geemap')

# Set matplotlib backend
import matplotlib
matplotlib.use('Agg')

# VoxCity imports
from voxcity.generator import get_voxcity
from voxcity.exporter.obj import export_obj
from voxcity.exporter.envimet import export_inx, generate_edb_file

# Initialize Rich console
console = Console()

class UNESCOGenerator:
    def __init__(self, quality_preset: Optional[str] = None):
        self.console = console
        self.df = None
        self.quality_manager = get_quality_manager() if QUALITY_SYSTEM_AVAILABLE else None
        self.quality_preset = quality_preset
        self.load_heritage_sites()
        
    def print_header(self):
        """Print beautiful header with quality info"""
        header_text = Text()
        header_text.append("🏛️ UNESCO Heritage Sites 3D Generator\n", style="bold blue")
        header_text.append("Generate detailed 3D models of World Heritage Sites\n", style="italic")
        
        if self.quality_preset and QUALITY_SYSTEM_AVAILABLE:
            preset = self.quality_manager.get_preset(self.quality_preset)
            header_text.append(f"Quality: {preset.name} - {preset.description}\n", style="bold yellow")
        
        header_text.append("Powered by Google Earth Engine + VoxCity", style="dim")
        
        panel = Panel(
            header_text,
            title="[bold green]UNESCO 3D Heritage Modeling[/bold green]",
            subtitle="[dim]By UNESCO Data & AI Specialist[/dim]",
            border_style="blue"
        )
        self.console.print(panel)
        self.console.print()

    def load_heritage_sites(self):
        """Load UNESCO heritage sites from CSV"""
        csv_path = Path("data/unesco_heritage_sites.csv")
        if not csv_path.exists():
            self.console.print("[red]❌ UNESCO heritage sites CSV not found at data/unesco_heritage_sites.csv[/red]")
            sys.exit(1)
        
        self.df = pd.read_csv(csv_path)
        self.console.print(f"[green]✅ Loaded {len(self.df)} UNESCO heritage sites[/green]")

    def show_heritage_sites(self):
        """Display available heritage sites"""
        table = Table(title="🌍 UNESCO World Heritage Sites")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Site Name", style="green")
        table.add_column("Country", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Year", style="blue")
        
        for idx, row in self.df.iterrows():
            site_type = "🏛️ Cultural" if row['Category'] == 'Cultural' else "🌿 Natural"
            table.add_row(
                str(idx),
                row['Title EN'][:40] + "..." if len(row['Title EN']) > 40 else row['Title EN'],
                row['Country Title EN'],
                site_type,
                str(row['Date'])
            )
        
        self.console.print(table)
        self.console.print()

    def interactive_quality_selection(self) -> Optional[str]:
        """Interactive quality preset selection"""
        if not QUALITY_SYSTEM_AVAILABLE:
            return None
            
        self.console.print("\n[bold cyan]📐 Quality Preset Selection[/bold cyan]")
        self.quality_manager.list_presets()
        
        quality_choice = Prompt.ask(
            "\nSelect quality preset",
            choices=["preview", "standard", "premium", "ultimate", "skip"],
            default="standard",
            show_choices=True
        )
        
        if quality_choice == "skip":
            self.console.print("[yellow]⏭️ Using .env file settings[/yellow]")
            return None
        
        self.quality_manager.show_preset_details(quality_choice)
        
        confirm = Confirm.ask(f"\nUse {quality_choice.upper()} quality preset?", default=True)
        if confirm:
            return quality_choice
        else:
            return self.interactive_quality_selection()

    def get_configuration(self):
        """Get configuration from quality preset or environment"""
        if self.quality_preset and QUALITY_SYSTEM_AVAILABLE:
            # Use quality preset
            preset = self.quality_manager.get_preset(self.quality_preset)
            config = {
                'zone_size': preset.zone_size,
                'mesh_size': preset.mesh_size,
                'building_source': preset.building_source,
                'land_cover_source': preset.land_cover_source,
                'canopy_height_source': preset.canopy_height_source,
                'dem_source': preset.dem_source,
                'dem_interpolation': preset.dem_interpolation,
                'output_dir': os.getenv('OUTPUT_DIR', 'output'),
                'project_id': os.getenv('EE_PROJECT_ID', 'coordinates3d-generator')
            }
            
            # Show quality preset being used
            self.console.print(f"[bold green]🎯 Using {preset.name} Quality Preset[/bold green]")
            
        else:
            # Use environment variables
            config = {
                'zone_size': int(os.getenv('ZONE_SIZE_METERS', 750)),
                'mesh_size': int(os.getenv('MESH_SIZE_METERS', 5)),
                'building_source': os.getenv('BUILDING_SOURCE', 'OpenStreetMap'),
                'land_cover_source': os.getenv('LAND_COVER_SOURCE', 'OpenStreetMap'),
                'canopy_height_source': os.getenv('CANOPY_HEIGHT_SOURCE', 'ETH Global Sentinel-2 10m'),
                'dem_source': os.getenv('DEM_SOURCE', 'FABDEM'),
                'dem_interpolation': os.getenv('DEM_INTERPOLATION', 'true').lower() == 'true',
                'output_dir': os.getenv('OUTPUT_DIR', 'output'),
                'project_id': os.getenv('EE_PROJECT_ID', 'coordinates3d-generator')
            }
            
            if not self.quality_preset:
                self.console.print("[blue]📄 Using .env configuration[/blue]")
        
        return config

    def parse_coordinates(self, coord_str: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse coordinates from CSV"""
        if pd.isna(coord_str):
            return None, None
        
        coord_str = coord_str.strip('()[]')
        
        for sep in [',', ';', ' ']:
            if sep in coord_str:
                parts = coord_str.split(sep)
                if len(parts) >= 2:
                    try:
                        lat = float(parts[0].strip())
                        lon = float(parts[1].strip())
                        
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            return lat, lon
                    except ValueError:
                        continue
        
        return None, None

    def create_rectangle_from_center(self, lat: float, lon: float, size_meters: int) -> List[Tuple[float, float]]:
        """Create rectangle vertices around center point"""
        lat_offset = (size_meters / 2) / 111000
        lon_offset = (size_meters / 2) / (111000 * abs(cos(radians(lat))))
        
        return [
            (lon - lon_offset, lat - lat_offset),  # SW
            (lon - lon_offset, lat + lat_offset),  # NW
            (lon + lon_offset, lat + lat_offset),  # NE
            (lon + lon_offset, lat - lat_offset)   # SE
        ]

    def display_site_info(self, row, config):
        """Display site information with quality details"""
        table = Table(title=f"🗺️ Site: {row['Title EN']}")
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Description", style="dim")
        
        lat, lon = self.parse_coordinates(row['Coordinates'])
        
        # Site information
        table.add_row("🏛️ Name", row['Title EN'], "UNESCO World Heritage Site")
        table.add_row("🌍 Country", row['Country Title EN'], "Location")
        table.add_row("📅 Inscribed", str(row['Date']), "Year added to UNESCO list")
        table.add_row("🏷️ Category", row['Category'], "Cultural or Natural heritage")
        table.add_row("📍 Coordinates", f"{lat:.4f}°, {lon:.4f}°", "GPS location")
        
        # Quality configuration
        zone_size = config['zone_size']
        mesh_size = config['mesh_size']
        voxel_count = (zone_size // mesh_size) ** 2
        
        table.add_row("🔲 Zone Size", f"{zone_size:,}m × {zone_size:,}m", f"Coverage: {(zone_size/1000):.2f}km²")
        table.add_row("🔬 Resolution", f"{mesh_size}m voxels", f"Detail level")
        table.add_row("📊 Voxels", f"{voxel_count:,}", "Total 3D grid cells")
        
        # Quality preset info
        if self.quality_preset and QUALITY_SYSTEM_AVAILABLE:
            preset = self.quality_manager.get_preset(self.quality_preset)
            table.add_row("⏱️ Est. Time", preset.estimated_time, f"{preset.name} quality")
            table.add_row("🎯 Use Case", preset.use_case, "Quality preset purpose")
        
        self.console.print(table)
        self.console.print()
        
        # Data sources table
        sources_table = Table(title="🗂️ Data Sources Configuration")
        sources_table.add_column("Type", style="cyan", no_wrap=True)
        sources_table.add_column("Source", style="green")
        sources_table.add_column("Quality", style="yellow")
        
        sources_table.add_row("🏗️ Buildings", config['building_source'], self._get_source_quality(config['building_source']))
        sources_table.add_row("🌍 Land Cover", config['land_cover_source'], self._get_source_quality(config['land_cover_source']))
        sources_table.add_row("🌳 Canopy", config['canopy_height_source'] or "None (disabled)", self._get_source_quality(config['canopy_height_source'] or "None"))
        sources_table.add_row("⛰️ Terrain", config['dem_source'], self._get_source_quality(config['dem_source']))
        sources_table.add_row("🔄 DEM Interp.", "✅ Enabled" if config['dem_interpolation'] else "❌ Disabled", 
                             "Enhanced terrain" if config['dem_interpolation'] else "Basic terrain")
        
        self.console.print(sources_table)
        self.console.print()

    def _get_source_quality(self, source: str) -> str:
        """Get quality indicator for data source"""
        if not source or source == "None":
            return "⚪ Disabled"
            
        high_quality = ["Microsoft Building Footprints", "High Resolution 1m Global Canopy Height Maps", 
                       "ESRI Land Cover", "DeltaDTM"]
        medium_quality = ["ETH Global Sentinel-2 10m", "FABDEM"]
        
        if any(hq in source for hq in high_quality):
            return "🔴 High"
        elif any(mq in source for mq in medium_quality):
            return "🟡 Medium"
        else:
            return "🔵 Standard"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def initialize_earth_engine(self, project_id: str):
        """Initialize Earth Engine with retry"""
        with self.console.status("[bold blue]🌍 Connecting to Google Earth Engine..."):
            os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
            os.environ['EE_PROJECT'] = project_id
            ee.Initialize(project=project_id)
            
            # Test connection
            test_image = ee.Image('USGS/SRTMGL1_003').select('elevation')
            band_names = test_image.bandNames()
            
        self.console.print("[green]✅ Earth Engine connected successfully![/green]")

    def generate_voxel_city(self, rectangle_vertices, config):
        """Generate voxel city with comprehensive fallback handling"""
        
        kwargs = {
            "output_dir": config['output_dir'], 
            "dem_interpolation": config['dem_interpolation']
        }
        
        # Define fallback strategies for common VoxCity errors
        fallback_strategies = [
            {
                "name": "Primary Configuration",
                "building_source": config['building_source'],
                "land_cover_source": config['land_cover_source'],
                "canopy_height_source": config['canopy_height_source'],
                "dem_source": config['dem_source']
            },
            {
                "name": "ETH Canopy Data",
                "building_source": config['building_source'],
                "land_cover_source": config['land_cover_source'],
                "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
                "dem_source": config['dem_source']
            },
            {
                "name": "OpenStreetMap Land Cover",
                "building_source": config['building_source'],
                "land_cover_source": "OpenStreetMap",
                "canopy_height_source": config['canopy_height_source'],
                "dem_source": config['dem_source']
            },
            {
                "name": "ETH Canopy + OSM Land Cover",
                "building_source": config['building_source'],
                "land_cover_source": "OpenStreetMap",
                "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
                "dem_source": config['dem_source']
            },
            {
                "name": "Basic OpenStreetMap Configuration",
                "building_source": "OpenStreetMap",
                "land_cover_source": "OpenStreetMap",
                "canopy_height_source": "ETH Global Sentinel-2 10m Canopy Height (2020)",
                "dem_source": "FABDEM"
            },
            {
                "name": "No Canopy Data",
                "building_source": config['building_source'],
                "land_cover_source": "OpenStreetMap",
                "canopy_height_source": None,
                "dem_source": config['dem_source']
            },
            {
                "name": "Minimal Reliable Configuration",
                "building_source": "OpenStreetMap",
                "land_cover_source": "OpenStreetMap",
                "canopy_height_source": None,
                "dem_source": "FABDEM"
            }
        ]
        
        for i, strategy in enumerate(fallback_strategies):
            try:
                if i == 0:
                    status_msg = "[bold green]🏗️ Generating 3D city model...[/bold green]"
                else:
                    self.console.print(f"[blue]🔄 Trying {strategy['name']}...[/blue]")
                    status_msg = f"[bold blue]🏗️ Generating with {strategy['name']}...[/bold blue]"
                
                with self.console.status(status_msg):
                    result = get_voxcity(
                        rectangle_vertices,
                        strategy['building_source'],
                        strategy['land_cover_source'],
                        strategy['canopy_height_source'],
                        strategy['dem_source'],
                        config['mesh_size'],
                        **kwargs
                    )
                
                if i == 0:
                    self.console.print("[green]✅ Primary generation successful![/green]")
                else:
                    self.console.print(f"[green]✅ Success with {strategy['name']}![/green]")
                    self.console.print(f"[yellow]ℹ️  Note: Using {strategy['land_cover_source']} land cover and {strategy['building_source']} buildings[/yellow]")
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                if i == 0:
                    self.console.print(f"[yellow]⚠️  Primary generation failed: {error_msg}[/yellow]")
                else:
                    self.console.print(f"[yellow]⚠️  {strategy['name']} failed: {error_msg}[/yellow]")
                
                # Special handling for VoxCity library errors
                if "land_cover_classes" in error_msg:
                    self.console.print("[blue]💡 Land cover classes issue detected - switching to OpenStreetMap sources[/blue]")
                elif "cannot access local variable 'image'" in error_msg:
                    self.console.print("[blue]💡 Canopy data access issue detected - switching to ETH Global data[/blue]")
                elif "image" in error_msg.lower() and "not associated with a value" in error_msg:
                    self.console.print("[blue]💡 Data source image loading issue - trying alternative sources[/blue]")
                
                # If this is the last strategy, raise the error
                if i == len(fallback_strategies) - 1:
                    self.console.print(f"[red]❌ All fallback strategies failed![/red]")
                    self.console.print(f"[red]Final error: {error_msg}[/red]")
                    raise e
                
                continue

    def export_models(self, voxcity_grid, building_height_grid, building_id_grid,
                     canopy_height_grid, land_cover_grid, dem_grid, config,
                     land_cover_source, rectangle_vertices, site_name):
        """Export 3D models"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            export_task = progress.add_task("📦 Exporting models...", total=2)
            
            # Export OBJ
            progress.update(export_task, description="📦 Exporting OBJ file...")
            try:
                export_obj(voxcity_grid, config['output_dir'], site_name, config['mesh_size'])
                obj_success = True
                self.console.print("[green]✅ OBJ file exported![/green]")
            except Exception as e:
                obj_success = False
                self.console.print(f"[red]❌ OBJ export failed: {e}[/red]")
            
            progress.advance(export_task)
            
            # Export ENVI-MET
            envimet_success = False
            if canopy_height_grid is not None:
                progress.update(export_task, description="🌍 Exporting ENVI-MET...")
                try:
                    envimet_kwargs = {
                        "output_directory": config['output_dir'],
                        "author_name": "UNESCO Data Specialist",
                        "model_description": f"3D model of {site_name}",
                        "domain_building_max_height_ratio": 2,
                        "useTelescoping_grid": True,
                        "verticalStretch": 20,
                        "min_grids_Z": 20,
                        "lad": 1.0
                    }
                    
                    export_inx(building_height_grid, building_id_grid, canopy_height_grid,
                              land_cover_grid, dem_grid, config['mesh_size'], land_cover_source,
                              rectangle_vertices, **envimet_kwargs)
                    generate_edb_file(**envimet_kwargs)
                    envimet_success = True
                    self.console.print("[green]✅ ENVI-MET exported![/green]")
                except Exception as e:
                    self.console.print(f"[yellow]⚠️ ENVI-MET failed: {e}[/yellow]")
            
            progress.advance(export_task)
        
        return obj_success, envimet_success

    def display_results(self, config, site_name: str, obj_success: bool, colored_success: bool = False):
        """Display results with quality info"""
        if obj_success:
            success_text = Text()
            success_text.append("🎉 3D Model Generated Successfully!\n", style="bold green")
            success_text.append(f"Site: {site_name}\n", style="bold")
            
            if self.quality_preset and QUALITY_SYSTEM_AVAILABLE:
                preset = self.quality_manager.get_preset(self.quality_preset)
                success_text.append(f"Quality: {preset.name} ({preset.detail_level})\n", style="yellow")
            
            panel = Panel(success_text, title="[bold green]✅ Success[/bold green]", border_style="green")
            self.console.print(panel)
            
            # File list with quality info
            table = Table(title=f"📁 Generated Files in {config['output_dir']}/")
            table.add_column("File", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Features", style="yellow")
            
            # Standard OBJ
            table.add_row(f"{site_name}.obj", "3D Model", "Standard geometry")
            table.add_row(f"{site_name}.mtl", "Materials", "Basic materials")
            
            # Quality-specific files
            if config['mesh_size'] <= 3:
                table.add_row("quality_info.txt", "Quality Report", "🏆 High detail model")
            
            # Enhanced version if exists
            enhanced_obj = Path(config['output_dir']) / f"{site_name}_enhanced.obj"
            if enhanced_obj.exists():
                table.add_row(f"{site_name}_enhanced.obj", "Enhanced Model", "🔄 Fixed orientation")
            
            self.console.print(table)
            
            # Viewing instructions with quality context
            viewing_text = Text()
            viewing_text.append("🎨 View Your 3D Models:\n", style="bold cyan")
            
            if config['mesh_size'] <= 3:
                viewing_text.append("⭐ HIGH DETAIL MODEL: ", style="bold green")
                viewing_text.append("Perfect for close inspection and analysis\n")
            elif config['mesh_size'] <= 5:
                viewing_text.append("⚡ BALANCED MODEL: ", style="bold yellow")
                viewing_text.append("Good balance of detail and performance\n")
            else:
                viewing_text.append("🚀 PREVIEW MODEL: ", style="bold blue")
                viewing_text.append("Quick overview, ideal for site exploration\n")
            
            viewing_text.append("• Online: ", style="bold")
            viewing_text.append("https://3dviewer.net/", style="link")
            viewing_text.append(f" (drag & drop {site_name}.obj)\n")
            viewing_text.append("• macOS: ", style="bold")
            viewing_text.append(f"open {config['output_dir']}/{site_name}.obj\n", style="code")
            viewing_text.append("• Blender: ", style="bold")
            viewing_text.append("File > Import > Wavefront (.obj)", style="italic")
            
            panel = Panel(viewing_text, title="[bold cyan]🎨 Next Steps[/bold cyan]", border_style="cyan")
            self.console.print(panel)

    def interactive_mode(self):
        """Interactive site selection with quality options"""
        self.show_heritage_sites()
        
        site_id = IntPrompt.ask(
            "Choose a heritage site (enter ID number)",
            default=1,
            show_default=True
        )
        
        if 0 <= site_id < len(self.df):
            row = self.df.iloc[site_id]
            
            # Quality selection if not already specified
            if not self.quality_preset and QUALITY_SYSTEM_AVAILABLE:
                self.quality_preset = self.interactive_quality_selection()
            
            return row
        else:
            self.console.print("[red]❌ Invalid site ID[/red]")
            return None

    def run(self, mode="interactive", site_id=None):
        """Main execution with quality system"""
        self.print_header()
        
        # Load environment
        load_dotenv()
        
        # Determine site to process
        if mode == "test":
            # Mont-Saint-Michel test
            row = self.df[self.df['Title EN'].str.contains('Mont-Saint-Michel', na=False)].iloc[0]
            self.console.print("[bold blue]🏰 Running Mont-Saint-Michel test[/bold blue]")
        elif mode == "site" and site_id is not None:
            if 0 <= site_id < len(self.df):
                row = self.df.iloc[site_id]
            else:
                self.console.print(f"[red]❌ Invalid site ID: {site_id}[/red]")
                return
        else:
            # Interactive mode
            row = self.interactive_mode()
            if row is None:
                return
        
        # Get coordinates
        lat, lon = self.parse_coordinates(row['Coordinates'])
        if lat is None or lon is None:
            self.console.print(f"[red]❌ Invalid coordinates: {row['Coordinates']}[/red]")
            return
        
        # Get configuration (from quality preset or environment)
        config = self.get_configuration()
        
        # Display site info with quality details
        self.display_site_info(row, config)
        
        # Initialize Earth Engine
        try:
            self.initialize_earth_engine(config['project_id'])
        except Exception as e:
            self.console.print(f"[red]❌ Earth Engine failed: {e}[/red]")
            self.console.print("[yellow]Run: poetry run earthengine authenticate[/yellow]")
            self.console.print(f"[yellow]Then: poetry run earthengine set_project {config['project_id']}[/yellow]")
            return
        
        # Create output directory
        os.makedirs(config['output_dir'], exist_ok=True)
        
        # Generate model
        rectangle_vertices = self.create_rectangle_from_center(lat, lon, config['zone_size'])
        site_name = row['Title EN'].replace(' ', '_').replace(',', '').replace("'", "")
        
        try:
            result = self.generate_voxel_city(rectangle_vertices, config)
            
            voxcity_grid, building_height_grid, building_min_height_grid, \
            building_id_grid, canopy_height_grid, land_cover_grid, dem_grid, building_gdf = result
            
            # Export models
            obj_success, envimet_success = self.export_models(
                voxcity_grid, building_height_grid, building_id_grid,
                canopy_height_grid, land_cover_grid, dem_grid, config,
                config['land_cover_source'], rectangle_vertices, site_name
            )
            
            # Save quality report
            if self.quality_preset and QUALITY_SYSTEM_AVAILABLE and obj_success:
                self._save_quality_report(config, site_name, row)
            
            # Show results
            self.display_results(config, site_name, obj_success)
            
        except Exception as e:
            error_msg = str(e)
            self.console.print(f"[red]❌ Generation failed: {error_msg}[/red]")
            
            # Provide specific guidance based on error type
            if "land_cover_classes" in error_msg:
                self.console.print("\n[bold yellow]🔍 Land Cover Classes Error Detected![/bold yellow]")
                self.console.print("This is a known issue with certain data sources in VoxCity.")
                self.console.print("\n[cyan]Recommended solutions:[/cyan]")
                self.console.print("1. Use PREVIEW quality: [bold]poetry run python main.py test --quality preview[/bold]")
                self.console.print("2. Apply standard preset: [bold]poetry run python quality_config.py apply standard[/bold]")
                self.console.print("3. Manual fix: Edit .env and set [bold]LAND_COVER_SOURCE=OpenStreetMap[/bold]")
            elif "cannot access local variable 'image'" in error_msg or "image" in error_msg.lower():
                self.console.print("\n[bold yellow]🔍 VoxCity Image Loading Error Detected![/bold yellow]")
                self.console.print("This is a known issue with certain canopy height data sources.")
                self.console.print("\n[cyan]Recommended solutions:[/cyan]")
                self.console.print("1. Use PREVIEW quality: [bold]poetry run python main.py test --quality preview[/bold]")
                self.console.print("2. Switch canopy source: Edit .env and set [bold]CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m[/bold]")
                self.console.print("3. Disable canopy: Edit .env and set [bold]CANOPY_HEIGHT_SOURCE=[/bold] (empty)")
            elif "canopy" in error_msg.lower():
                self.console.print("\n[cyan]Canopy data issue:[/cyan] Try --quality preview for simpler data sources")
            elif "earth engine" in error_msg.lower():
                self.console.print("\n[cyan]Earth Engine issue:[/cyan] poetry run earthengine authenticate")
            else:
                self.console.print("\n[cyan]General troubleshooting:[/cyan]")
                self.console.print("1. Try PREVIEW quality: [bold]poetry run python main.py test --quality preview[/bold]")
                self.console.print("2. Check internet connection")
                self.console.print("3. Verify Earth Engine authentication")

    def _save_quality_report(self, config, site_name, row):
        """Save quality report for the generated model"""
        preset = self.quality_manager.get_preset(self.quality_preset)
        
        report_path = Path(config['output_dir']) / f"{site_name}_quality_report.txt"
        
        with open(report_path, 'w') as f:
            f.write(f"UNESCO Heritage Site 3D Model Quality Report\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Site: {row['Title EN']}\n")
            f.write(f"Country: {row['Country Title EN']}\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Quality Preset: {preset.name}\n")
            f.write(f"Description: {preset.description}\n")
            f.write(f"Use Case: {preset.use_case}\n\n")
            
            f.write(f"Technical Specifications:\n")
            f.write(f"- Zone Size: {config['zone_size']}m × {config['zone_size']}m\n")
            f.write(f"- Coverage: {preset.coverage_km2:.2f} km²\n")
            f.write(f"- Resolution: {config['mesh_size']}m voxels\n")
            f.write(f"- Detail Level: {preset.detail_level}\n")
            f.write(f"- Total Voxels: {preset.voxel_count:,}\n\n")
            
            f.write(f"Data Sources:\n")
            f.write(f"- Buildings: {config['building_source']}\n")
            f.write(f"- Land Cover: {config['land_cover_source']}\n")
            f.write(f"- Canopy Height: {config['canopy_height_source']}\n")
            f.write(f"- Terrain: {config['dem_source']}\n")
            f.write(f"- DEM Interpolation: {'Enabled' if config['dem_interpolation'] else 'Disabled'}\n")
        
        self.console.print(f"[green]📄 Quality report saved: {report_path}[/green]")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="UNESCO Heritage Sites 3D Generator with Quality Presets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive mode
  python main.py test                               # Mont-Saint-Michel test
  python main.py 4                                  # Machu Picchu (site ID 4)
  python main.py 4 --quality premium               # Machu Picchu with premium quality
  python main.py --quality ultimate                # Interactive with ultimate quality
  python main.py --list-quality                    # List available quality presets
  python main.py --quality-details standard        # Show standard preset details
        """
    )
    
    parser.add_argument('site', nargs='?', help='Site ID number or "test" for Mont-Saint-Michel')
    parser.add_argument('--quality', choices=['preview', 'standard', 'premium', 'ultimate'],
                       help='Quality preset to use')
    parser.add_argument('--list-quality', action='store_true', help='List available quality presets')
    parser.add_argument('--quality-details', choices=['preview', 'standard', 'premium', 'ultimate'],
                       help='Show details for a specific quality preset')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Handle quality system commands
    if args.list_quality:
        if QUALITY_SYSTEM_AVAILABLE:
            manager = get_quality_manager()
            manager.list_presets()
        else:
            console.print("[red]❌ Quality system not available. Install quality_config.py[/red]")
        return
    
    if args.quality_details:
        if QUALITY_SYSTEM_AVAILABLE:
            manager = get_quality_manager()
            manager.show_preset_details(args.quality_details)
        else:
            console.print("[red]❌ Quality system not available. Install quality_config.py[/red]")
        return
    
    # Initialize generator with quality preset
    generator = UNESCOGenerator(quality_preset=args.quality)
    
    # Determine mode
    if args.site == "test":
        generator.run("test")
    elif args.site and args.site.isdigit():
        generator.run("site", int(args.site))
    elif args.site:
        console.print(f"[red]❌ Invalid site identifier: {args.site}[/red]")
        console.print("[yellow]Use a number (site ID) or 'test' for Mont-Saint-Michel[/yellow]")
    else:
        generator.run("interactive")

if __name__ == "__main__":
    main()