import argparse
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from app.core.rule_engine import RuleEngine
from app.config.config_manager import ConfigManager
from app.core.input_loader import collect_targets

def main():
    parser = argparse.ArgumentParser(description="DETECH: Analizador Estático Multilenguaje")
    parser.add_argument("target", help="Ruta al archivo o directorio a analizar")
    parser.add_argument("--export-json", help="Ruta para exportar los resultados en formato JSON", type=str)
    
    args = parser.parse_args()
    target_path = Path(args.target)
    
    if not target_path.exists():
        print(f"Error: La ruta '{args.target}' no existe.")
        sys.exit(1)
        
    config = ConfigManager()
    engine = RuleEngine(config)
    console = Console()
    
    with console.status("[bold green]Analizando archivos...") as status:
        try:
            files_to_analyze = collect_targets(target_path)
        except Exception as e:
            console.print(f"[red]Error recolectando archivos: {e}[/red]")
            sys.exit(1)
            
        all_results = []
        for file in files_to_analyze:
            try:
                result = engine.analyze_file(file)
                all_results.append(result)
            except Exception as e:
                console.print(f"[red]Error analizando {file}: {e}[/red]")
    
    if not all_results:
        console.print("[yellow]No se encontraron archivos válidos para analizar.[/yellow]")
        sys.exit(0)
        
    # Draw the table
    table = Table(title="Resultados del Análisis DETECH")
    table.add_column("Archivo", style="cyan")
    table.add_column("Línea", justify="right", style="magenta")
    table.add_column("Regla", style="blue")
    table.add_column("Severidad")
    table.add_column("Mensaje")
    
    total_anomalies = 0
    for res in all_results:
        for anomaly in res.anomalies:
            total_anomalies += 1
            sev_color = "red" if anomaly.severity == "critical" else "yellow" if anomaly.severity == "warning" else "white"
            
            table.add_row(
                Path(anomaly.file).name,
                str(anomaly.line),
                anomaly.rule_id,
                f"[{sev_color}]{anomaly.severity.upper()}[/{sev_color}]",
                anomaly.message
            )
            
    console.print(table)
    console.print(f"\n[bold]Total de archivos analizados:[/bold] {len(all_results)}")
    console.print(f"[bold]Total de anomalías detectadas:[/bold] {total_anomalies}")
    
    if args.export_json:
        export_path = Path(args.export_json)
        export_data = [res.model_dump() for res in all_results]
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4)
        console.print(f"[green]Reporte exportado exitosamente a {export_path}[/green]")

if __name__ == "__main__":
    main()
