# DETECH — Análisis de Anomalías en Código Python

**DETECH** es una herramienta de análisis estático rápido diseñada para ayudar a los desarrolladores a identificar problemas de legibilidad, complejidad, código muerto y posibles fallos de seguridad en sus programas de Python, sin necesidad de ejecutar el código.

## Características Principales

- **Resiliente a errores de sintaxis:** Utiliza el módulo `tokenize` en lugar de un parser de árbol abstracto (AST), permitiendo escanear archivos incluso si están incompletos o en proceso de escritura.
- **5 Categorías de detección:** Legibilidad, Complejidad, Seguridad, Estilo y Código Muerto.
- **Reglas personalizables:** Puedes añadir tus propias reglas usando expresiones regulares en el archivo de configuración `detech.yaml`.
- **UI:** Utiliza un sistema Drag & Drop, modo oscuro, vista de resultados con filtros y métricas por batch.
- **Reportes:** Genera un reporte detallado en HTML, que puede exportarse directamente a PDF usando la función de impresión nativa del navegador.

## Stack Tecnológico

| Capa            | Tecnología                 |
| --------------- | -------------------------- |
| Backend API     | FastAPI (Python 3.11+)     |
| Tokenización    | `tokenize` (stdlib) + `re` |
| Configuración   | YAML (`PyYAML`)            |
| Plantillas HTML | Jinja2                     |
| Generación PDF  | Impresión Nativa de Navegador |
| Frontend        | HTML5 + CSS3 + Vanilla JS  |
| Testing         | pytest + pytest-cov        |

## Instalación

1. Clona el repositorio e instala las dependencias:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

(Opcional) Instala la herramienta en modo paquete con: `pip install -e .`

## Uso

Inicia el servidor backend (FastAPI):

```bash
uvicorn app.main:app --reload
```

Abre tu navegador en [http://localhost:8000](http://localhost:8000) para acceder a la interfaz. Sube archivos `.py` para obtener resultados.

## Estructura del Proyecto

```text
detech/
├── app/
│   ├── main.py              # Backend FastAPI y UI handler
│   ├── core/                # InputLoader, Tokenizer, Metrics, RuleEngine
│   ├── detectors/           # Módulos de reglas (legibility, security, etc.)
│   ├── reports/             # Generador de reportes Jinja2
│   └── api/                 # Endpoints REST (/analyze, /report, /config)
├── frontend/                # HTML, CSS (Glassmorphism), JS
├── docs/                    # Documentación
├── tests/                   # Suite de pruebas automatizadas y fixtures
├── detech.yaml              # Archivo donde customizas reglas y umbrales
└── pyproject.toml           # Configuración de empaquetado del proyecto
```
