#!/usr/bin/env python3
"""Script CLI para generar reportes con ReportAgent y FastMCP."""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path

# Añadir project root al path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.agents.report.agent import ReportAgent
from app.agents.core.mcp_client import MCPClient
from app.config.settings import REPORTS_DIR


def setup_logging(verbose: bool = False):
    """Configura logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main(args):
    """Función principal."""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Generando reporte para: {args.consultant}")
    logger.info(f"FastMCP URL: {args.fastmcp_url}")
    
    try:
        # Crear cliente MCP
        async with MCPClient(base_url=args.fastmcp_url) as mcp_client:
            # Crear agente
            agent = ReportAgent(mcp_client=mcp_client)
            
            # Generar reporte
            report = await agent.generate_report(
                consultant_name=args.consultant,
                report_type=args.type
            )
            
            # Guardar reporte
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                timestamp = report.get('generated_at', '').replace(':', '-').split('.')[0]
                filename = f"{args.consultant.lower().replace(' ', '_')}_reporte_{timestamp}.json"
                output_path = REPORTS_DIR / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Reporte guardado en: {output_path}")
            
            # Imprimir resumen si se solicita
            if args.print_summary:
                print("\n" + "="*60)
                print("RESUMEN DEL REPORTE")
                print("="*60)
                print(f"Consultor: {report['consultant']}")
                print(f"Fecha: {report['generated_at']}")
                print(f"Tipo: {report['type']}")
                print(f"Filas SQL: {report['data']['sql_rows']}")
                print(f"Evidencias: {report['data']['evidence_count']}")
                print(f"Gráficos: {len(report.get('charts', {}))}")
                print(f"Versión: {report['metadata'].get('version')}")
                print(f"MCP URL: {report['metadata'].get('mcp_url')}")
                
                if report.get('sections', {}).get('summary'):
                    print("\n[RESUMEN EJECUTIVO]")
                    summary = report['sections']['summary']
                    preview = summary[:500] + "..." if len(summary) > 500 else summary
                    print(preview)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generando reporte: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generador de reportes con ReportAgent y FastMCP"
    )
    
    parser.add_argument(
        "--consultant",
        required=True,
        help="Nombre del consultor"
    )
    parser.add_argument(
        "--type",
        choices=["preview", "final"],
        default="preview",
        help="Tipo de reporte (default: preview)"
    )
    parser.add_argument(
        "--output",
        help="Archivo de salida (JSON). Si no se especifica, se genera automáticamente."
    )
    parser.add_argument(
        "--fastmcp-url",
        default="http://localhost:8000",
        help="URL del servidor FastMCP (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Imprimir resumen del reporte en consola"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activar logging detallado"
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)