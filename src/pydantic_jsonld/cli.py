"""
Command-line interface for pydantic-jsonld.
"""

import json
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("CLI dependencies not installed. Install with: pip install pydantic-jsonld[cli]")
    sys.exit(1)

from .models import JsonLDModel


console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """
    Pydantic JSON-LD: Generate JSON-LD contexts and SHACL shapes from Pydantic models.
    """
    pass


@main.command()
@click.argument("module_path", type=str)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./contexts"),
    help="Output directory for context files",
)
@click.option(
    "--model-names",
    "-m",
    multiple=True,
    help="Specific model names to export (default: all JsonLDModel subclasses)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "jsonld"]),
    default="jsonld",
    help="Output format",
)
@click.option("--indent", type=int, default=2, help="JSON indentation")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing files")
def export_contexts(
    module_path: str,
    output_dir: Path,
    model_names: tuple[str, ...],
    format: str,
    indent: int,
    dry_run: bool,
) -> None:
    """
    Export JSON-LD contexts from Pydantic models.
    
    MODULE_PATH should be in the format 'package.module' (e.g., 'myapp.models')
    """
    try:
        # Import the module
        module = importlib.import_module(module_path)
        
        # Find JsonLDModel subclasses
        models = _find_jsonld_models(module, model_names)
        
        if not models:
            console.print("[red]No JsonLDModel subclasses found in the module[/red]")
            return
        
        # Create output directory if not dry run
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        table = Table(title="Context Export Results")
        table.add_column("Model", style="cyan")
        table.add_column("Output File", style="green")
        table.add_column("Status", style="yellow")
        
        for model_class in models:
            try:
                # Generate context
                context = model_class.export_context()
                
                # Generate filename
                filename = f"{model_class.__name__.lower()}.{format}"
                output_file = output_dir / filename
                
                if dry_run:
                    table.add_row(model_class.__name__, str(output_file), "DRY RUN")
                    console.print(f"\n[bold]{model_class.__name__}[/bold] context:")
                    console.print(Panel(json.dumps(context, indent=indent), expand=False))
                else:
                    # Write to file
                    with open(output_file, "w") as f:
                        json.dump(context, f, indent=indent)
                    
                    table.add_row(model_class.__name__, str(output_file), "✓ Success")
                    
            except Exception as e:
                table.add_row(model_class.__name__, "N/A", f"✗ Error: {str(e)}")
        
        console.print(table)
        
    except ImportError as e:
        console.print(f"[red]Error importing module '{module_path}': {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("module_path", type=str)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./shacl"),
    help="Output directory for SHACL files",
)
@click.option(
    "--model-names",
    "-m",
    multiple=True,
    help="Specific model names to export (default: all JsonLDModel subclasses)",
)
@click.option("--indent", type=int, default=2, help="JSON indentation")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing files")
def export_shacl(
    module_path: str,
    output_dir: Path,
    model_names: tuple[str, ...],
    indent: int,
    dry_run: bool,
) -> None:
    """
    Export SHACL shapes from Pydantic models.
    
    MODULE_PATH should be in the format 'package.module' (e.g., 'myapp.models')
    """
    try:
        # Import the module
        module = importlib.import_module(module_path)
        
        # Find JsonLDModel subclasses
        models = _find_jsonld_models(module, model_names)
        
        if not models:
            console.print("[red]No JsonLDModel subclasses found in the module[/red]")
            return
        
        # Create output directory if not dry run
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        table = Table(title="SHACL Export Results")
        table.add_column("Model", style="cyan")
        table.add_column("Output File", style="green")
        table.add_column("Status", style="yellow")
        
        for model_class in models:
            try:
                # Generate SHACL shape
                shape = model_class.export_shacl()
                
                # Generate filename
                filename = f"{model_class.__name__.lower()}_shape.jsonld"
                output_file = output_dir / filename
                
                if dry_run:
                    table.add_row(model_class.__name__, str(output_file), "DRY RUN")
                    console.print(f"\n[bold]{model_class.__name__}[/bold] SHACL shape:")
                    console.print(Panel(json.dumps(shape, indent=indent), expand=False))
                else:
                    # Write to file
                    with open(output_file, "w") as f:
                        json.dump(shape, f, indent=indent)
                    
                    table.add_row(model_class.__name__, str(output_file), "✓ Success")
                    
            except Exception as e:
                table.add_row(model_class.__name__, "N/A", f"✗ Error: {str(e)}")
        
        console.print(table)
        
    except ImportError as e:
        console.print(f"[red]Error importing module '{module_path}': {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("module_path", type=str)
@click.option(
    "--model-names",
    "-m",
    multiple=True,
    help="Specific model names to inspect (default: all JsonLDModel subclasses)",
)
def inspect(module_path: str, model_names: tuple[str, ...]) -> None:
    """
    Inspect JsonLDModel classes and their JSON-LD annotations.
    
    MODULE_PATH should be in the format 'package.module' (e.g., 'myapp.models')
    """
    try:
        # Import the module
        module = importlib.import_module(module_path)
        
        # Find JsonLDModel subclasses
        models = _find_jsonld_models(module, model_names)
        
        if not models:
            console.print("[red]No JsonLDModel subclasses found in the module[/red]")
            return
        
        for model_class in models:
            console.print(f"\n[bold cyan]{model_class.__name__}[/bold cyan]")
            console.print(f"Module: {model_class.__module__}")
            
            # Show JSON-LD configuration
            config_table = Table(title="JSON-LD Configuration")
            config_table.add_column("Property", style="cyan")
            config_table.add_column("Value", style="green")
            
            config_table.add_row("Base IRI", str(getattr(model_class, '_json_ld_base', 'None')))
            config_table.add_row("Vocab IRI", str(getattr(model_class, '_json_ld_vocab', 'None')))
            config_table.add_row("Remote Contexts", str(getattr(model_class, '_json_ld_remote_contexts', [])))
            config_table.add_row("Prefixes", str(getattr(model_class, '_json_ld_prefixes', {})))
            
            console.print(config_table)
            
            # Show field annotations
            from .models import _JSONLD_META_KEY
            
            field_table = Table(title="Field Annotations")
            field_table.add_column("Field", style="cyan")
            field_table.add_column("Type", style="yellow")
            field_table.add_column("IRI", style="green")
            field_table.add_column("JSON-LD Type", style="magenta")
            field_table.add_column("Container", style="blue")
            
            for field_name, field_info in model_class.model_fields.items():
                jsonld_meta = field_info.metadata.get(_JSONLD_META_KEY, {})
                
                field_table.add_row(
                    field_name,
                    str(field_info.annotation),
                    jsonld_meta.get('iri', 'N/A'),
                    jsonld_meta.get('type', 'N/A'),
                    jsonld_meta.get('container', 'N/A')
                )
            
            console.print(field_table)
        
    except ImportError as e:
        console.print(f"[red]Error importing module '{module_path}': {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _find_jsonld_models(module: Any, model_names: tuple[str, ...]) -> List[Type[JsonLDModel]]:
    """
    Find JsonLDModel subclasses in a module.
    
    Args:
        module: The imported module
        model_names: Specific model names to find (empty means all)
        
    Returns:
        List of JsonLDModel subclasses
    """
    models = []
    
    for name in dir(module):
        if model_names and name not in model_names:
            continue
            
        obj = getattr(module, name)
        
        # Check if it's a class and a subclass of JsonLDModel
        if (
            isinstance(obj, type) and
            issubclass(obj, JsonLDModel) and
            obj is not JsonLDModel
        ):
            models.append(obj)
    
    return models


if __name__ == "__main__":
    main()