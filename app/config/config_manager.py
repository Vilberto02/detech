import re
from pathlib import Path
from typing import Any, Dict, List

import yaml


_DEFAULTS_PATH = Path(__file__).parent / "defaults.yaml"
_USER_CONFIG_NAME = "detech.yaml"


def _load_yaml(path: Path) -> Dict:
    """Carga un archivo YAML y retorna su contenido como dict."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Fusiona `override` sobre `base` de forma recursiva.
    Los valores de `override` tienen precedencia.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class ConfigManager:
    """
    Gestiona la configuración de DETECH.

    Carga los valores por defecto desde `defaults.yaml` y los fusiona con
    el archivo `detech.yaml` del usuario si existe en la ruta de trabajo.
    """

    def __init__(self, project_root: str | Path | None = None):
        """
        Args:
            project_root: Directorio raíz del proyecto a analizar.
                          Si es None, solo se usan los valores por defecto.
        """
        self._config = _load_yaml(_DEFAULTS_PATH)

        if project_root:
            user_config_path = Path(project_root) / _USER_CONFIG_NAME
            if user_config_path.exists():
                user_config = _load_yaml(user_config_path)
                self._config = _deep_merge(self._config, user_config)

    @property
    def thresholds(self) -> Dict[str, Any]:
        return self._config.get("thresholds", {})

    @property
    def rules(self) -> Dict[str, Dict[str, bool]]:
        return self._config.get("rules", {})

    @property
    def custom_patterns(self) -> List[Dict]:
        return self._config.get("custom_patterns", [])

    def get_threshold(self, key: str, default: Any = None) -> Any:
        """Obtiene un umbral por nombre."""
        return self.thresholds.get(key, default)

    def is_rule_enabled(self, category: str, rule: str) -> bool:
        """Verifica si una regla específica está habilitada."""
        return self.rules.get(category, {}).get(rule, True)

    def validate_custom_patterns(self) -> List[str]:
        """
        Valida que los patrones personalizados tengan regex válidas.

        Returns:
            Lista de errores de validación (vacía si todo está bien).
        """
        errors = []
        for pattern in self.custom_patterns:
            pid = pattern.get("id", "<sin id>")
            regex = pattern.get("pattern", "")
            try:
                re.compile(regex)
            except re.error as e:
                errors.append(f"Patrón '{pid}': regex inválida — {e}")
        return errors

    def as_dict(self) -> Dict:
        """Retorna la configuración completa como diccionario."""
        return dict(self._config)
