# Réplica temporal — HTML/CSS/JS

Este proyecto convierte el Excel `Plantilla_Encargo02_Replica.xlsx` en una web estática.

## Estructura

```txt
replica_web/
├─ index.html
├─ styles.css
├─ app.js
├─ data/
│  └─ data.json
├─ assets/
│  └─ images/
└─ Plantilla_Encargo02_Replica.xlsx
```

## Cómo verlo localmente

No abras `index.html` con doble click, porque `fetch()` puede bloquear la carga del JSON.
Usa un servidor local:

```bash
cd replica_web
python3 -m http.server 8000
```

Luego abre:

```txt
http://localhost:8000
```

## Cómo actualizar desde el Excel

1. Reemplaza `Plantilla_Encargo02_Replica.xlsx`.
2. Ejecuta el script `build_web_from_excel.py` desde Python ajustando la ruta de entrada/salida si es necesario.
3. Sube `index.html`, `styles.css`, `app.js`, `data/` y `assets/` a GitHub Pages.

## Nota técnica

El navegador puede leer datos desde un `.xlsx` con librerías como SheetJS, pero las imágenes embebidas son más complejas. Por eso este proyecto usa una etapa de conversión: extrae imágenes del Excel, las guarda como archivos `.jpg` y crea un `data.json` que la web puede cargar rápido.
