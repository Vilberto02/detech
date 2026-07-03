"""
Interfaz base para todos los detectores de anomalías.
Todos los detectores concretos deben heredar de BaseDetector.
"""

from abc import ABC, abstractmethod
from typing import List

from ..core.models import Anomaly
from ..core.tokenizer import Token
from ..config.config_manager import ConfigManager


class BaseDetector(ABC):
    """
    Interfaz base para detectores de anomalías (patrón Strategy).

    Cada detector recibe el código fuente tokenizado y las métricas calculadas,
    y retorna una lista de anomalías encontradas.
    """

    #: Nombre de la categoría que maneja este detector (para filtrado por reglas)
    category: str = ""

    def __init__(self, config: ConfigManager):
        self.config = config

    @abstractmethod
    def detect(
        self,
        filepath: str,
        lines: List[str],
        tokens: List[Token],
        metrics: dict,
    ) -> List[Anomaly]:
        """
        Ejecuta la detección de anomalías.

        Args:
            filepath: Ruta del archivo analizado.
            lines: Líneas del archivo fuente.
            tokens: Tokens léxicos del archivo.
            metrics: Métricas precalculadas (LOC, complejidad, funciones, etc.).

        Returns:
            Lista de objetos Anomaly encontrados.
        """
        ...

    def is_enabled(self, rule: str) -> bool:
        """Verifica si una regla específica de este detector está habilitada."""
        return self.config.is_rule_enabled(self.category, rule)
