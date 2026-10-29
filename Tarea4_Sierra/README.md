# Tarea 4 – Introducción a Series de Tiempo

**Business Intelligence · Universidad del Istmo de Guatemala**
**Autor:** José Sierra

Simulación de procesos AR(1), y limpieza, descomposición, pronóstico (B1, B2, M1, M2, SARIMA) y análisis RFM de la venta neta diaria de *Online Retail* (UCI).

## Contenido

```
.
├── README.md
├── Tarea4_Sierra.ipynb   # Todo el análisis, Partes 0 a 6
├── limpiar.py                       # Función limpiar(df) (en su propio archivo)
├── ts_utils.py                      # ACF, Ljung-Box y AR(1) implementados con numpy
├── tarea4.tex                       # Documento: derivaciones, análisis, tablas y figuras
├── tarea4.pdf                       # Documento compilado
├── figuras/                         # Generadas por el notebook
├── tablas/                          # Tablas .tex y cifras.tex, generadas por el notebook
├── pyproject.toml · uv.lock · .python-version
└── .gitignore
```

## Datos

El archivo original **no se incluye** en el repositorio (está en `.gitignore`). Descárguenlo de
[UCI – Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) y coloquen `Online Retail.xlsx` dentro de una carpeta `data/`.

## Cómo ejecutarlo

### Local con uv

```bash
uv sync                  # crea el entorno con las versiones exactas de uv.lock
uv run jupyter lab       # abrir Tarea4_Sierra.ipynb y ejecutar todas las celdas
```

### Google Colab

1. Abrir el notebook desde GitHub en Colab.
2. En la primera celda de código, cambiar `REPO_URL` por la URL de este repositorio. Esa celda clona el repo para tener `limpiar.py` y `ts_utils.py`.
3. *Entorno de ejecución → Ejecutar todas*. Cuando lo pida, subir `Online Retail.xlsx`.

La primera lectura del .xlsx tarda 1–2 minutos; después queda una copia en `data/online_retail.pkl`. Todo el notebook tarda unos minutos, sobre todo por los reajustes de SARIMA en la Parte 5.

### Documento

Después de correr el notebook, compilar `tarea4.tex` (por ejemplo en Overleaf, subiendo también `figuras/` y `tablas/`). El documento lee las cifras de `tablas/cifras.tex`, así que se actualiza solo. Lo que falte aparece en rojo como **[correr notebook]**.

## Semillas

- Parte 0: una semilla por escenario (`SEMILLAS` en el notebook: 1000, 1050, 1090, 1100, 2001, 2002).
- Parte 5 (validación cruzada aleatoria): semillas 0 a 9.
- Parte 6 (desempate de quintiles): `numpy.random.default_rng(2026)`.

## Uso de IA

Usamos Claude como apoyo para entender el enunciado, estructurar el código y redactar borradores de las explicaciones. Ejecutamos el notebook con los datos originales y revisamos cada cifra e interpretación del documento contra los resultados.
