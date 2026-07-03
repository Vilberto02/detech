"""
Carga y normalización de archivos de código fuente.
Soporta archivo único o directorio completo (batch).
"""

import os
from pathlib import Path
from typing import List, Tuple


SUPPORTED_EXTENSION = ".py"


def load_file(filepath: str | Path) -> Tuple[str, List[str]]:
    """
    Carga un archivo de código fuente Python.

    Args:
        filepath: Ruta al archivo .py.

    Returns:
        Tupla (contenido_completo, lista_de_líneas).

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si la extensión no es .py.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

    if path.suffix.lower() != SUPPORTED_EXTENSION:
        raise ValueError(
            f"Extensión no soportada '{path.suffix}'. Solo se admiten archivos .py"
        )

    # Intentar detectar encoding — probar UTF-8 primero, luego Latin-1 como fallback
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            content = path.read_text(encoding=encoding)
            lines = content.splitlines()
            return content, lines
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        f"No se pudo decodificar el archivo {filepath} con los encodings disponibles."
    )


def load_directory(dirpath: str | Path, recursive: bool = True) -> List[Path]:
    """
    Retorna una lista de archivos .py encontrados en el directorio.

    Args:
        dirpath: Ruta al directorio a explorar.
        recursive: Si True, busca recursivamente en subdirectorios.

    Returns:
        Lista de Path a archivos .py encontrados.

    Raises:
        NotADirectoryError: Si la ruta no es un directorio.
    """
    path = Path(dirpath)

    if not path.is_dir():
        raise NotADirectoryError(f"La ruta no es un directorio: {dirpath}")

    pattern = "**/*.py" if recursive else "*.py"
    files = sorted(path.glob(pattern))

    # Excluir archivos en directorios de entorno virtual o caché
    excluded_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules", ".tox"}
    filtered = [
        f for f in files
        if not any(part in excluded_dirs for part in f.parts)
    ]

    return filtered


def collect_targets(path_input: str | Path) -> List[Path]:
    """
    Dado un path (archivo o directorio), retorna la lista de archivos .py a analizar.

    Args:
        path_input: Ruta a un archivo .py o a un directorio.

    Returns:
        Lista de Path con los archivos a procesar.
    """
    path = Path(path_input)

    if path.is_file():
        if path.suffix.lower() != SUPPORTED_EXTENSION:
            raise ValueError(f"El archivo '{path}' no tiene extensión .py")
        return [path]
    elif path.is_dir():
        return load_directory(path)
    else:
        raise FileNotFoundError(f"La ruta no existe: {path_input}")
