#!/usr/bin/env python3
"""
Script simple para sincronizar proyecto a carpeta Github respetando .gitignore
Uso: python sync_github.py
"""

import os
import shutil
import fnmatch
from pathlib import Path

# Configuración
SOURCE = r"C:\Users\JuanEstebanGarciaGal\Documents\IBM\Report-generator"
TARGET = r"C:\Users\JuanEstebanGarciaGal\Documents\Github\Report-generator"

def load_gitignore():
    """Carga reglas del .gitignore"""
    gitignore = Path(SOURCE) / '.gitignore'
    rules = []
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    rules.append(line)
    
    # Reglas adicionales que siempre ignorar
    rules.extend(['.git', '.git/*'])
    
    return rules

def should_ignore(path, rules):
    """Verifica si un archivo debe ser ignorado"""
    path = path.replace('\\', '/')
    
    for rule in rules:
        # Reglas que terminan con / son solo para directorios
        if rule.endswith('/'):
            rule = rule[:-1]
            if fnmatch.fnmatch(path, rule) or path.startswith(rule + '/'):
                return True
        else:
            # Reglas normales
            if fnmatch.fnmatch(path, rule):
                return True
            # Verificar si algún directorio padre coincide
            parts = path.split('/')
            for i in range(len(parts)):
                parent_path = '/'.join(parts[:i+1])
                if fnmatch.fnmatch(parent_path, rule):
                    return True
    
    return False

def main():
    print(f"Sincronizando desde: {SOURCE}")
    print(f"Hacia: {TARGET}")
    print("-" * 50)
    
    # Cargar reglas
    rules = load_gitignore()
    print(f"Reglas .gitignore: {len(rules)}")
    
    # Crear destino
    Path(TARGET).mkdir(parents=True, exist_ok=True)
    
    stats = {'total': 0, 'copiados': 0, 'ignorados': 0, 'errores': 0}
    
    # Recorrer archivos
    for root, dirs, files in os.walk(SOURCE):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs 
                  if not should_ignore(str(Path(root).relative_to(SOURCE) / d), rules)]
        
        for file in files:
            source_file = Path(root) / file
            rel_path = source_file.relative_to(SOURCE)
            rel_str = str(rel_path).replace('\\', '/')
            
            stats['total'] += 1
            
            # Verificar si ignorar
            if should_ignore(rel_str, rules):
                stats['ignorados'] += 1
                continue
            
            # Copiar archivo
            target_file = Path(TARGET) / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Solo copiar si es nuevo o modificado
                if not target_file.exists() or source_file.stat().st_mtime > target_file.stat().st_mtime:
                    shutil.copy2(source_file, target_file)
                    stats['copiados'] += 1
                    print(f"✓ {rel_path}")
            except Exception as e:
                stats['errores'] += 1
                print(f"✗ Error en {rel_path}: {e}")
    
    # Resumen
    print("-" * 50)
    print(f"Total: {stats['total']}, Copiados: {stats['copiados']}, Ignorados: {stats['ignorados']}, Errores: {stats['errores']}")
    print("¡Listo!")

if __name__ == '__main__':
    main()
