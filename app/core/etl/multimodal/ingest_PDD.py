from __future__ import annotations

import io
import json
import logging
import re
import unicodedata
import hashlib
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from types import SimpleNamespace

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from app.config.settings_etl import UPLOADS_MULTIMODAL_DIR, DATA_LOG_PATH, CHROMA_COLLECTIONS
from app.core.ia.vision import get_vision_provider
from .vectorize import vectorize_content, prepare_metadata, prepare_solution_metadata, IngestionResult

log = logging.getLogger(__name__)
MULTIMODAL_LOG_FILE = DATA_LOG_PATH / "multimodal_ingestion_log.json"

TMP_DIR = (DATA_LOG_PATH / "tmp_images")
TMP_DIR.mkdir(parents=True, exist_ok=True)

HEADING_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)*)[.)\s]+(.+?)(?:\s+\d+)?\s*$",
    re.IGNORECASE
)
SKIP_TOKENS = {"confidencial", "cb consultores chile.", "grupo epm", "grupo saesa"}

SECTION_KEYWORDS = {
    "1": ["control de la plantilla", "control de versiones", "historial de cambios"],
    "2": ["descripción y evidencia", "evidencia hallazgo", "descripción hallazgo"],
    "3": ["respuesta consultoría", "respuesta consultoria", "solución"]
}

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))

def _norm(s: str) -> str:
    s2 = _strip_accents(str(s or ""))
    s2 = re.sub(r"\s+", "_", s2.strip().lower())
    s2 = re.sub(r"[^a-z0-9_\-\.]+", "", s2)
    return s2

def _digits(s: str) -> str:
    m = re.search(r"\d+",str(s or ""))
    return m.group(0) if m else ""

def _normalize_title(s: str) -> str:
    """Normaliza el título removiendo prefijos numéricos y caracteres especiales al inicio."""
    s = (s or "").strip()
    # Remover prefijos como "02_02_07_" o números al inicio
    s = re.sub(r"^\d+(?:_\d+)*_?", "", s)
    # Remover guiones y espacios al inicio
    s = re.sub(r"^[-–\s]+", "", s)
    return s.lower().strip()

def _content_sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

#Extrae el titulo del documento para revisar los footers y no volver a tener en cuenta el titulo 
def _is_footer_or_disclaimer(text: str, document_title: Optional[str] = None) -> bool:
    s = " ".join((text or "").lower().split())
    if not s:
        return True  # Vacío
    
    if s.startswith("página ") or s.startswith("pagina ") or any(tok in s for tok in SKIP_TOKENS):
        return True
    
    if document_title:
        title_norm = _normalize_title(document_title)
        text_norm = _normalize_title(text)
        # Solo filtrar si es exactamente igual al título (para evitar perder contenido como transacciones)
        if text_norm == title_norm:
            return True  # Es footer/header
    
    return False
def _detect_heading(line: str) -> Tuple[Optional[str], Optional[str]]:
    clean_line = re.sub(r'\s+', ' ', line.strip())
    m = HEADING_RE.match(clean_line)
    return(m.group(1), m.group(2).strip()) if m else(None)

def _infer_section_from_content(text: str, is_marker_check: bool = False) -> Optional[str]:
    text_lower = _strip_accents(text.lower())
    
    matches  = []
    for section,keywords in SECTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matches.append(section)
    
    if not matches:
        return None
    
    if is_marker_check:
        words = [w for w in text.split() if w.strip()]
        word_count = len(words)

        if word_count < 10 and len(matches) ==1:
            return matches[0]
        return None
    return matches[0]

def _page_of(el) -> Optional[int]:
    try:
        p = getattr(getattr(el, "metadata", None), "page number", None)
        return p
    except Exception:
        return None
   

def _get_section_parent(path: str) -> str:
    if path != "title":
        return path
    parts = path.split(".")
    return parts[0] if parts else path

def _extract_metadata_from_path(file_path: Path) -> Dict[str, str]:
    """
    TODO: Extrae metadata desde la estructura del path:
    by_responsable/{Responsable}/{ID_Caso-Descripcion}/{Fecha}/{Archivo}
    by_ticket/{Responsable}/{ID_Caso-Descripcion}/{Fecha}/{Archivo}
    
    Retorna:
    - responsable_original: Nombre sin normalizar
    - responsable_clean: Nombre limpio
    - defecto_id_digits: ID limpio
    - defecto_original: Carpeta completa
    - tipo_organizacion: "by_responsable" o "by_ticket"
    """
    # TODO: Implementar extracción de metadata del path
    pass

def _extract_business_metadata(elements: List[Any]) -> Dict[str, str]:
    """
    TODO: Extrae módulo y proyecto desde las tablas de metadata del documento.
    Busca en las primeras tablas campos como:
    - "Nombre de Proyecto", "Proyecto"
    - "Sistema y/o Módulo", "Módulo", "Frente"
    """
    # TODO: Implementar extracción de metadata de negocio
    pass

def _extract_id_reporte_from_path(file_path: Path) -> Optional[str]:
    """TODO: Mantener para compatibilidad, pero _extract_metadata_from_path es más completo"""
    # TODO: Implementar extracción de ID de reporte
    pass

def _extract_image_bytes(el) -> bytes | None:
    # TODO: Implementar extracción de bytes de imagen
    pass

def _materialize_image(el) -> Path | None:
    # TODO: Implementar materialización de imagen en archivo temporal
    pass

def _docx_inline_images_as_elements(docx_path: Path) -> list:
    # TODO: Implementar extracción de imágenes inline de DOCX
    pass

def partition_file(path: Path) -> List[Any]:
    # TODO: Implementar particionamiento de archivo (PDF, DOCX, etc.)
    pass

def _element_to_markdown(el: Any) -> str:
    # TODO: Implementar conversión de elemento a Markdown
    pass

async def _describe_images_async(images: List[Any]) -> List[str]:
    # TODO: Implementar descripción asíncrona de imágenes
    pass

async def process_document_by_section_async(elements: List[Any]) -> Tuple[List[str], List[Dict]]:
    """
    TODO: Nueva estrategia:
    1. Detectar encabezados en TOC/índice
    2. Asignar elementos por contenido (no por posición)
    3. Las tablas con títulos de sección marcan los límites
    """
    # Extraer título del documento: el texto más frecuente (asumiendo que el título se repite)
    text_counts = {}
    for elem in elements:
        if hasattr(elem, 'text') and elem.text.strip():
            text = elem.text.strip()
            text_counts[text] = text_counts.get(text, 0) + 1
    
    # Tomar el texto más frecuente como título, si aparece al menos 2 veces
    document_title = None
    if text_counts:
        most_common = max(text_counts, key=text_counts.get)
        if text_counts[most_common] >= 2:
            document_title = most_common
    
    # Filtrar elementos que no son footers/disclaimers
    filtered_elements = []
    for elem in elements:
        if hasattr(elem, 'text') and _is_footer_or_disclaimer(elem.text, document_title):
            continue
        filtered_elements.append(elem)
    
    # TODO: Procesar secciones (por ahora, devolver todo como una sección)
    sections = [" ".join([elem.text for elem in filtered_elements if hasattr(elem, 'text')])]
    metadata = [{"section": "main", "title": document_title or "Unknown"}]
    
    return sections, metadata

def _save_log(data: Dict):
    # TODO: Implementar guardado de log en archivo JSON
    pass

def _files_in(d: Path) -> List[Path]:
    # TODO: Implementar lista de archivos en directorio
    pass

async def _process_dir(root: Path, responsable: Optional[str], defecto: Optional[str], meta_preparer, collection_name: str) -> Dict[str, int]:
    # TODO: Implementar procesamiento recursivo de directorio
    pass

async def ingest_evidence_tree(responsable: Optional[str] = None, defecto: Optional[str] = None) -> IngestionResult:
    # TODO: Implementar ingesta de evidencia
    pass

async def ingest_solutions_tree(responsable: Optional[str] = None, defecto: Optional[str] = None) -> IngestionResult:
    # TODO: Implementar ingesta de soluciones
    pass