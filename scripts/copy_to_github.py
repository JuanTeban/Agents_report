#!/usr/bin/env python3
"""
Script para copiar el proyecto completo a una carpeta en GitHub
respetando el .gitignore y excluyendo la carpeta .git
"""

import os
import shutil
import fnmatch
from pathlib import Path
import argparse


class GitIgnoreMatcher:
    """Clase para manejar patrones de .gitignore"""
    
    def __init__(self, gitignore_path):
        self.patterns = []
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Normalizar patrones
                        if line.startswith('/'):
                            line = line[1:]
                        if line.endswith('/'):
                            line = line[:-1]
                        self.patterns.append(line)
    
    def should_ignore(self, file_path):
        """Verifica si un archivo/carpeta debe ser ignorado"""
        # Siempre ignorar .git
        if '.git' in file_path.parts:
            return True
            
        # Convertir path a string relativo para comparación
        rel_path = str(file_path).replace('\\', '/')
        
        for pattern in self.patterns:
            # Patrón exacto
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
            # Patrón con ** para subdirectorios
            if '**' in pattern:
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
        
        return False


def copy_project_to_github(source_dir, target_dir, dry_run=False):
    """
    Copia el proyecto completo respetando .gitignore
    
    Args:
        source_dir: Directorio fuente
        target_dir: Directorio destino
        dry_run: Si True, solo muestra qué se copiaría sin hacerlo
    """
    
    source_path = Path(source_dir).resolve()
    target_path = Path(target_dir).resolve()
    
    # Crear matcher de .gitignore
    gitignore_path = source_path / '.gitignore'
    ignore_matcher = GitIgnoreMatcher(gitignore_path)
    
    # Crear directorio destino si no existe
    if not dry_run:
        target_path.mkdir(parents=True, exist_ok=True)
    
    copied_files = 0
    skipped_files = 0
    
    print(f"Copiando proyecto desde: {source_path}")
    print(f"Destino: {target_path}")
    print(f"Modo: {'DRY RUN' if dry_run else 'COPIA REAL'}")
    print("-" * 50)
    
    # Recorrer todos los archivos y carpetas
    for root, dirs, files in os.walk(source_path):
        root_path = Path(root)
        
        # Filtrar directorios que deben ser ignorados
        dirs[:] = [d for d in dirs if not ignore_matcher.should_ignore(root_path / d)]
        
        # Crear estructura de directorios
        rel_root = root_path.relative_to(source_path)
        target_root = target_path / rel_root
        
        if not dry_run and rel_root != Path('.'):
            target_root.mkdir(parents=True, exist_ok=True)
        
        # Copiar archivos
        for file in files:
            source_file = root_path / file
            target_file = target_root / file
            
            # Verificar si debe ignorarse
            if ignore_matcher.should_ignore(source_file):
                print(f"IGNORADO: {source_file.relative_to(source_path)}")
                skipped_files += 1
                continue
            
            if dry_run:
                print(f"COPIARÍA: {source_file.relative_to(source_path)}")
            else:
                try:
                    shutil.copy2(source_file, target_file)
                    print(f"COPIADO: {source_file.relative_to(source_path)}")
                except Exception as e:
                    print(f"ERROR copiando {source_file}: {e}")
                    skipped_files += 1
                    continue
            
            copied_files += 1
    
    print("-" * 50)
    print(f"Resumen:")
    print(f"  Archivos copiados: {copied_files}")
    print(f"  Archivos ignorados: {skipped_files}")
    
    if dry_run:
        print(f"\nPara realizar la copia real, ejecuta sin --dry-run")


def main():
    parser = argparse.ArgumentParser(
        description="Copia el proyecto a GitHub respetando .gitignore"
    )
    parser.add_argument(
        "--source", 
        default=".", 
        help="Directorio fuente (por defecto: directorio actual)"
    )
    parser.add_argument(
        "--target", 
        default=r"C:\Users\JuanEstebanGarciaGal\Documents\Github\Report-generator",
        help="Directorio destino"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Solo muestra qué se copiaría sin hacer la copia real"
    )
    
    args = parser.parse_args()
    
    # Validar directorio fuente
    if not os.path.exists(args.source):
        print(f"ERROR: El directorio fuente '{args.source}' no existe")
        return 1
    
    # Verificar que existe .gitignore
    gitignore_path = Path(args.source) / '.gitignore'
    if not gitignore_path.exists():
        print(f"ADVERTENCIA: No se encontró .gitignore en {args.source}")
    
    try:
        copy_project_to_github(args.source, args.target, args.dry_run)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
