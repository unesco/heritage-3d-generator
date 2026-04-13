#!/usr/bin/env python3
"""
🛠️ UNESCO Heritage Sites 3D Generator Setup Script
Sets up quality presets and validates installation

Usage:
    python setup.py                    # Interactive setup
    python setup.py --preset standard  # Apply specific preset
    python setup.py --test             # Test installation
    python setup.py --validate         # Validate all systems
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.prompt import Confirm

console = Console()

def print_header():
    """Print setup header"""
    header_text = Text()
    header_text.append("🛠️ UNESCO Heritage Sites 3D Generator Setup\n", style="bold blue")
    header_text.append("Quality Configuration System Installation\n", style="italic")
    header_text.append("Preparing your environment for heritage site modeling", style="dim")
    
    panel = Panel(
        header_text,
        title="[bold green]Setup & Configuration[/bold green]",
        subtitle="[dim]By UNESCO Data & AI Specialist[/dim]",
        border_style="blue"
    )
    console.print(panel)
    console.print()

def check_dependencies():
    """Check if all required dependencies are installed"""
    console.print("[bold cyan]🔍 Checking Dependencies[/bold cyan]")
    
    required_packages = [
        ("rich", "Rich console library"),
        ("pandas", "Data manipulation"),
        ("python-dotenv", "Environment variables"),
        ("voxcity", "VoxCity 3D generation"),
        ("tenacity", "Retry logic"),
        ("ee", "Google Earth Engine")
    ]
    
    missing_packages = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Checking packages...", total=len(required_packages))
        
        for package, description in required_packages:
            progress.update(task, description=f"Checking {package}...")
            try:
                __import__(package)
                console.print(f"[green]✅ {package}[/green] - {description}")
            except ImportError:
                console.print(f"[red]❌ {package}[/red] - {description}")
                missing_packages.append(package)
            progress.advance(task)
    
    if missing_packages:
        console.print(f"\n[red]❌ Missing packages: {', '.join(missing_packages)}[/red]")
        console.print("[yellow]Run: poetry install[/yellow]")
        return False
    else:
        console.print("\n[green]✅ All dependencies installed![/green]")
        return True

def validate_project_structure():
    """Validate project file structure"""
    console.print("\n[bold cyan]📁 Validating Project Structure[/bold cyan]")
    
    required_files = [
        ("main.py", "Main application script"),
        ("quality_config.py", "Quality configuration system"),
        ("data/unesco_heritage_sites.csv", "UNESCO sites database"),
        (".env", "Environment configuration"),
        ("pyproject.toml", "Poetry project file")
    ]
    
    required_dirs = [
        ("output", "Generated models directory"),
        ("data", "Data files directory"),
        ("wiki", "Documentation directory")
    ]
    
    missing_items = []
    
    # Check files
    for file_path, description in required_files:
        if Path(file_path).exists():
            console.print(f"[green]✅ {file_path}[/green] - {description}")
        else:
            console.print(f"[red]❌ {file_path}[/red] - {description}")
            missing_items.append(file_path)
    
    # Check directories
    for dir_path, description in required_dirs:
        if Path(dir_path).exists():
            console.print(f"[green]✅ {dir_path}/[/green] - {description}")
        else:
            console.print(f"[yellow]⚠️ {dir_path}/[/yellow] - {description} (will create)")
            Path(dir_path).mkdir(exist_ok=True)
    
    if missing_items:
        console.print(f"\n[red]❌ Missing required files: {', '.join(missing_items)}[/red]")
        return False
    else:
        console.print(f"\n[green]✅ Project structure validated![/green]")
        return True

def test_quality_system():
    """Test the quality configuration system"""
    console.print("\n[bold cyan]🎯 Testing Quality System[/bold cyan]")
    
    try:
        from quality_config import QualityManager, get_quality_manager
        
        manager = get_quality_manager()
        console.print("[green]✅ Quality system imported successfully[/green]")
        
        # Test preset access
        for preset_name in ["preview", "standard", "premium", "ultimate"]:
            preset = manager.get_preset(preset_name)
            console.print(f"[green]✅ {preset_name.upper()}[/green] - {preset.description}")
        
        console.print("\n[green]✅ Quality system fully functional![/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Quality system error: {e}[/red]")
        return False

def setup_environment():
    """Set up or validate environment configuration"""
    console.print("\n[bold cyan]⚙️ Environment Configuration[/bold cyan]")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        console.print("[yellow]⚠️ .env file not found, creating default...[/yellow]")
        
        default_env = """# Earth Engine Project ID (required)
# Change this to your Earth Engine project ID
EE_PROJECT_ID=coordinates3d-generator

# Suppress warnings
PYTHONWARNINGS=ignore::UserWarning:geemap.*

# Quality preset: STANDARD - Balanced quality and speed
# Applied on: 2025-01-01 12:00:00

# Zone parameters
ZONE_SIZE_METERS=750
MESH_SIZE_METERS=5

# Data sources
BUILDING_SOURCE=OpenStreetMap
LAND_COVER_SOURCE=OpenStreetMap
CANOPY_HEIGHT_SOURCE=ETH Global Sentinel-2 10m
DEM_SOURCE=FABDEM
DEM_INTERPOLATION=true

# Output directory
OUTPUT_DIR=output
"""
        with open(env_path, 'w') as f:
            f.write(default_env)
        
        console.print("[green]✅ Created default .env file with STANDARD quality preset[/green]")
    else:
        console.print("[green]✅ .env file exists[/green]")
    
    # Check for required environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    ee_project = os.getenv('EE_PROJECT_ID')
    if ee_project:
        console.print(f"[green]✅ Earth Engine project: {ee_project}[/green]")
    else:
        console.print("[red]❌ EE_PROJECT_ID not set in .env file[/red]")
        return False
    
    return True

def interactive_preset_setup():
    """Interactive quality preset selection and application"""
    console.print("\n[bold cyan]🎯 Quality Preset Setup[/bold cyan]")
    
    try:
        from quality_config import get_quality_manager
        manager = get_quality_manager()
        
        console.print("\nAvailable Quality Presets:")
        manager.list_presets()
        
        console.print("\n[bold yellow]Would you like to apply a quality preset to your .env file?[/bold yellow]")
        console.print("This will override current settings with optimized configurations.")
        
        if Confirm.ask("Apply quality preset?", default=False):
            from rich.prompt import Prompt
            
            preset_choice = Prompt.ask(
                "Select quality preset",
                choices=["preview", "standard", "premium", "ultimate"],
                default="standard",
                show_choices=True
            )
            
            manager.apply_preset_to_env(preset_choice)
            return True
        else:
            console.print("[blue]📄 Keeping current .env settings[/blue]")
            return True
            
    except Exception as e:
        console.print(f"[red]❌ Quality preset setup failed: {e}[/red]")
        return False

def run_test_generation():
    """Run a quick test generation"""
    console.print("\n[bold cyan]🧪 Test Generation[/bold cyan]")
    
    if not Confirm.ask("Run Mont-Saint-Michel test generation?", default=False):
        console.print("[blue]⏭️ Skipping test generation[/blue]")
        return True
    
    try:
        console.print("[yellow]🏰 Running Mont-Saint-Michel test...[/yellow]")
        console.print("[dim]This will take 1-3 minutes depending on your quality settings[/dim]")
        
        # Import and run test
        os.system("poetry run python main.py test")
        
        console.print("[green]✅ Test generation completed! Check output/ directory[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Test generation failed: {e}[/red]")
        console.print("[yellow]💡 Try running manually: poetry run python main.py test[/yellow]")
        return False

def display_next_steps():
    """Display next steps and usage examples"""
    next_steps_text = Text()
    next_steps_text.append("🎉 Setup Complete! Next Steps:\n\n", style="bold green")
    
    next_steps_text.append("📖 Basic Usage:\n", style="bold cyan")
    next_steps_text.append("• poetry run python main.py                     # Interactive mode\n")
    next_steps_text.append("• poetry run python main.py test                # Quick test\n")
    next_steps_text.append("• poetry run python main.py 4                   # Specific site\n\n")
    
    next_steps_text.append("🎯 Quality Presets:\n", style="bold yellow")
    next_steps_text.append("• poetry run python main.py --quality preview   # Fast preview\n")
    next_steps_text.append("• poetry run python main.py --quality standard  # Balanced\n")
    next_steps_text.append("• poetry run python main.py --quality premium   # High quality\n")
    next_steps_text.append("• poetry run python main.py --quality ultimate  # Maximum quality\n\n")
    
    next_steps_text.append("ℹ️ Information Commands:\n", style="bold blue")
    next_steps_text.append("• poetry run python main.py --list-quality      # List presets\n")
    next_steps_text.append("• poetry run python main.py --quality-details standard\n")
    next_steps_text.append("• poetry run python quality_config.py           # Quality system CLI\n\n")
    
    next_steps_text.append("📁 Generated files will be in the output/ directory\n", style="dim")
    next_steps_text.append("🌐 View 3D models at: https://3dviewer.net/", style="link")
    
    panel = Panel(
        next_steps_text,
        title="[bold green]🚀 Ready to Generate 3D Heritage Models![/bold green]",
        border_style="green"
    )
    console.print(panel)

def main():
    parser = argparse.ArgumentParser(description="Setup UNESCO Heritage Sites 3D Generator")
    parser.add_argument('--preset', choices=['preview', 'standard', 'premium', 'ultimate'],
                       help='Apply specific quality preset')
    parser.add_argument('--test', action='store_true', help='Run test generation')
    parser.add_argument('--validate', action='store_true', help='Validate installation only')
    
    args = parser.parse_args()
    
    print_header()
    
    # Validation steps
    deps_ok = check_dependencies()
    structure_ok = validate_project_structure()
    env_ok = setup_environment()
    quality_ok = test_quality_system()
    
    if not all([deps_ok, structure_ok, env_ok, quality_ok]):
        console.print("\n[red]❌ Setup validation failed. Please fix the issues above.[/red]")
        sys.exit(1)
    
    # If just validating, stop here
    if args.validate:
        console.print("\n[green]✅ All systems validated successfully![/green]")
        return
    
    # Apply preset if specified
    if args.preset:
        try:
            from quality_config import get_quality_manager
            manager = get_quality_manager()
            manager.apply_preset_to_env(args.preset)
        except Exception as e:
            console.print(f"[red]❌ Failed to apply preset: {e}[/red]")
            sys.exit(1)
    else:
        # Interactive preset setup
        interactive_preset_setup()
    
    # Run test if requested
    if args.test:
        run_test_generation()
    
    # Show next steps
    display_next_steps()

if __name__ == "__main__":
    main()
