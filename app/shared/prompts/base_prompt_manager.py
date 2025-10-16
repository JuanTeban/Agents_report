import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BasePromptManager:
    """
    Clase base genérica para cargar plantillas de prompts
    desde un archivo JSON específico.
    """
    def __init__(self, prompts_path: Path):
        self._templates: Dict[str, str] = {}
        self._load_prompts_from_file(prompts_path)

    def _load_prompts_from_file(self, prompts_path: Path):
        try:
            with open(prompts_path, "r", encoding="utf-8") as f:
                self._templates = json.load(f)
            logger.info(f"Prompts cargados para {self.__class__.__name__} desde: {prompts_path}")
        except FileNotFoundError:
            logger.error(f"Archivo de prompts no encontrado en: {prompts_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando el archivo JSON de prompts: {e}")
            raise

    def _get_template(self, key: str) -> str:
        """Obtiene una plantilla de prompt de forma segura."""
        template = self._templates.get(key)
        if not template:
            logger.error(f"Clave de prompt '{key}' no encontrada.")
            raise KeyError(f"Clave de prompt '{key}' no encontrada.")
        return template