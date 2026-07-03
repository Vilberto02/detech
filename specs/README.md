# DETECH — Especificaciones del sistema

## Descripción General

**DETECH** es una herramienta de soporte al programador para la detección estática de anomalías en código fuente Python. Su objetivo es minimizar las posibles anomalías mediante el análisis del texto del archivo fuente, sin requerir ejecución del programa ni construcción de un árbol sintáctico formal.

La herramienta expone una **interfaz web** desde la cual el programador puede subir uno o varios archivos (o directorios completos), configurar los umbrales y reglas de análisis, y descargar un reporte en formato **HTML o PDF**.

## Contexto

En el ámbito del desarrollo de programas, bibliotecas y componentes, surge la necesidad de adoptar herramientas que constituyan un soporte al programador. A medida que aumenta la complejidad de los programas, la revisión y el monitoreo se hacen más difíciles, impactando en los tiempos de desarrollo y en la calidad del producto final.

## Objetivo

Diseñar e implementar una herramienta de soporte al programador que permita detectar y reportar posibles anomalías en el código fuente de manera estática, asistiendo al desarrollador durante la etapa de escritura y revisión del código.

## Restricciones del Sistema

| Restricción                         | Descripción                                                                                                                                                            |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sin análisis sintáctico formal      | No se construirá ni utilizará un árbol sintáctico abstracto (AST) ni un parser de gramática formal. El análisis se realiza mediante tokenización léxica y heurísticas. |
| Sin análisis en tiempo de ejecución | El sistema no ejecuta el programa bajo ninguna circunstancia. Todo el análisis es puramente estático.                                                                  |
| Entrada por archivo                 | El código fuente se provee como archivo(s) de texto plano `.py`. El sistema puede procesar un archivo individual o un directorio completo (batch).                     |

## Decisiones de Diseño

| Aspecto                     | Decisión                                                        |
| --------------------------- | --------------------------------------------------------------- |
| **Lenguaje objetivo**       | Python (enfoque inicial)                                        |
| **Interfaz de usuario**     | Interfaz Web (HTML + CSS + JS, backend FastAPI)                 |
| **Formatos de reporte**     | HTML y PDF (exportables)                                        |
| **Severidad de anomalías**  | Tres niveles: **Crítico**, **Advertencia**, **Informativo**     |
| **Umbrales configurables**  | Mediante el archivo `detech.yaml` editable por el usuario       |
| **Patrones configurables**  | Extensible por el usuario mediante `custom_patterns` en el YAML |
| **Procesamiento por lotes** | Análisis de múltiples archivos o directorios completos          |

## Enfoque de Análisis

El motor de DETECH opera en los siguientes niveles de análisis, respetando las restricciones definidas:

1. **Análisis Léxico (Tokenización)**: Uso del módulo `tokenize` de la biblioteca estándar de Python, complementado con expresiones regulares para patrones adicionales. No constituye un parser sintáctico formal, sino un descompositor de tokens.

2. **Análisis Heurístico**: Aplicación de reglas configurables sobre los tokens y la estructura textual del código para identificar anomalías conocidas. Cada regla puede ser activada o desactivada individualmente.

3. **Análisis Métrico**: Cálculo de métricas cuantitativas del código (líneas de código, complejidad ciclomática estimada, profundidad de anidamiento, número de parámetros) para detectar valores fuera del umbral configurado.

4. **Análisis Estadístico** _(fase futura)_: Detección de valores atípicos (outliers) comparando métricas entre múltiples archivos del mismo proyecto en procesamiento por lotes.

## Categorías de Anomalías

### 1. Legibilidad y Mantenibilidad

| Anomalía                                    | Umbral por Defecto          | Severidad   |
| ------------------------------------------- | --------------------------- | ----------- |
| Función con exceso de líneas                | 50 líneas                   | Advertencia |
| Archivo excesivamente extenso               | 500 líneas                  | Advertencia |
| Nombre de variable demasiado corto          | 1–2 chars (fuera de bucles) | Informativo |
| Función sin docstring                       | —                           | Informativo |
| Línea que supera el límite (PEP 8)          | 79 caracteres               | Informativo |
| Indentación inconsistente (tabs + espacios) | —                           | Advertencia |

### 2. Complejidad

| Anomalía                              | Umbral por Defecto        | Severidad   |
| ------------------------------------- | ------------------------- | ----------- |
| Alta complejidad ciclomática estimada | 10 estructuras de control | Crítico     |
| Anidamiento excesivo                  | 4 niveles                 | Advertencia |
| Función con demasiados parámetros     | 5 parámetros              | Advertencia |
| Acoplamiento excesivo (imports)       | 15 módulos distintos      | Advertencia |

### 3. Código Muerto o Redundante

| Anomalía                                               | Severidad   |
| ------------------------------------------------------ | ----------- |
| Bloques de código comentado (lógica desactivada)       | Advertencia |
| Variable declarada sin uso posterior                   | Advertencia |
| Import sin referencia en el archivo                    | Advertencia |
| Anotaciones pendientes: `TODO`, `FIXME`, `HACK`, `XXX` | Informativo |

### 4. Seguridad

| Anomalía                                                              | Severidad |
| --------------------------------------------------------------------- | --------- |
| Credencial hardcodeada (`password=`, `api_key=`, `secret=` + literal) | Crítico   |
| Uso de función peligrosa (`eval()`, `exec()`, `__import__()`)         | Crítico   |
| Concatenación directa en consultas SQL                                | Crítico   |

### 5. Estilo y Convenciones

| Anomalía                                                | Severidad   |
| ------------------------------------------------------- | ----------- |
| Convención de nombres inconsistente (mezcla de estilos) | Informativo |
| Archivo sin docstring de módulo                         | Informativo |
| Código duplicado (bloques de alta similitud léxica)     | Advertencia |

## Patrones Personalizados

El usuario puede definir reglas adicionales en `detech.yaml` bajo la clave `custom_patterns`, especificando:

- **ID** único de la regla
- **Nombre** descriptivo
- **Patrón** (expresión regular)
- **Severidad** (`critical`, `warning`, `info`)
- **Mensaje** a mostrar al detectar la anomalía

## Arquitectura de Módulos

| Módulo                 | Rol                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------- |
| `InputLoader`          | Carga de archivos `.py` individuales o directorios (batch), detección de encoding     |
| `Tokenizer`            | Tokenización léxica via `tokenize` stdlib + regex auxiliares                          |
| `MetricsCalculator`    | Cálculo de métricas: LOC, complejidad estimada, anidamiento, parámetros               |
| `RuleEngine`           | Registro y orquestación de detectores (patrón Strategy + Plugin)                      |
| `AnomalyDetector` (×5) | Un detector por categoría: Legibilidad, Complejidad, Código Muerto, Seguridad, Estilo |
| `ConfigManager`        | Lectura/escritura de `detech.yaml` con umbrales y reglas activas                      |
| `ReportGenerator`      | Genera reportes HTML (Jinja2) y PDF (WeasyPrint)                                      |

## Entradas y Salidas

### Entradas

- Archivo(s) de código fuente `.py` o directorio completo (batch)
- Archivo de configuración `detech.yaml` (umbrales, reglas activas, patrones personalizados)

### Salidas

- Reporte de anomalías con:
  - Ruta y número de línea del hallazgo
  - Categoría y tipo de anomalía
  - Nivel de severidad (Crítico / Advertencia / Informativo)
  - Descripción del problema y fragmento de código relevante
- Formatos de exportación: **HTML** y **PDF**
- Resumen estadístico por categoría y por archivo (en modo batch)

## Stack Tecnológico

| Capa            | Tecnología                 |
| --------------- | -------------------------- |
| Backend API     | FastAPI (Python 3.11+)     |
| Tokenización    | `tokenize` (stdlib) + `re` |
| Configuración   | YAML (`PyYAML`)            |
| Plantillas HTML | Jinja2                     |
| Generación PDF  | WeasyPrint                 |
| Frontend        | HTML5 + CSS3 + Vanilla JS  |
| Testing         | pytest + pytest-cov        |
