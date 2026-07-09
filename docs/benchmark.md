# Benchmark de DETECH

Resultados de ejecutar DETECH sobre los archivos de prueba de `examples/`
(anomalías **intencionales**, usadas como verdad de referencia) y sobre el
propio código fuente de la herramienta (`app/`, _dogfooding_).

Generado el 2026-07-09 con la configuración por defecto (`defaults.yaml`).
LOC = líneas de código efectivas (sin comentarios ni líneas en blanco) /
líneas totales. La complejidad ciclomática es la estimación léxica a nivel
de archivo.

## Archivos de ejemplo (anomalías intencionales)

| Archivo                    | Lenguaje   | LOC (código/total) | Complejidad | Críticos | Advertencias | Informativos |
| -------------------------- | ---------- | -----------------: | ----------: | -------: | -----------: | -----------: |
| `examples/complex_api.py`  | Python     |              59/77 |          15 |        5 |            3 |           13 |
| `examples/ejemplo.go`      | Go         |              27/38 |           4 |        4 |            0 |            5 |
| `examples/ejemplo.js`      | JavaScript |              29/45 |           6 |        4 |            0 |            2 |
| `examples/ejemplo.rs`      | Rust       |              21/32 |           3 |        4 |            2 |            7 |
| `examples/legacy_system.c` | C          |              45/69 |          13 |        5 |            1 |            3 |
| `examples/microservice.go` | Go         |              43/61 |           9 |        4 |            1 |           25 |
| **Total examples/**        | 5 lenguajes |           224/322 |           — |   **26** |            7 |           55 |

Los 26 hallazgos críticos corresponden uno a uno con las anomalías sembradas
en los ejemplos: 12 credenciales hardcodeadas (`SEC001`), 6 usos de funciones
peligrosas (`SEC002`), 6 construcciones SQL inyectables (`SEC003`) y 2 de
complejidad ciclomática (`CPX001`). No hay falsos negativos sobre este
conjunto: la detección funciona en los 5 lenguajes.

## Dogfooding: DETECH analizándose a sí mismo

| Objetivo             | Archivos | LOC (código/total) | Críticos | Advertencias | Informativos |
| -------------------- | -------: | -----------------: | -------: | -----------: | -----------: |
| `app/` (código propio) |     24 |          1802/2221 |    **9** |           41 |          311 |

Los 9 críticos de `app/` son todos `CPX001` (funciones con complejidad
ciclomática estimada entre 11 y 17, p. ej. `find_function_end` del
tokenizer): deuda de diseño real y conocida, no falsos positivos. **Ninguno
es de seguridad**: al inicio de la fase de refactorización la herramienta se
acusaba a sí misma de 8 credenciales hardcodeadas inexistentes (constantes
como `NAME_TOKEN = "NAME"`); tras el filtro de plausibilidad del valor y la
clasificación por contexto léxico, los falsos positivos de seguridad sobre
`app/` son 0.

### Cómo reproducir

```bash
python -m app.cli examples/ --export-json examples.json
python -m app.cli app/ --export-json app.json
```
