# MapForge

**A modern geospatial extraction engine.**
Extract, visualize, and export high-precision urban data from OpenStreetMap (OSM) for any location on Earth.

![Status](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Leaflet](https://img.shields.io/badge/Frontend-Leaflet.js-green)

## 🚀 Key Features

### 🎨 Modern UI/UX
* **Smart Dark Mode:** Automatically detects system theme. The MapForge logo adapts visibility (White on Dark / Dark on Light) without color distortion.
* **Global Loader:** A full-screen, reliable loading overlay that prevents interaction crashes during heavy data processing.
* **Mobile Optimized:** Fully responsive layout with bottom-sheet controls for phones.

### 🗺️ Advanced Navigation
* **Search & Pin:** Locate any city or coordinate. Drops a **Red Marker Pin** silently (click to see name) and flies to the location.
* **Global View:** One-click reset to the world view.
* **Selection Zoom:** Instantly center the camera on your drawn shape.

### 🛠️ Powerful Tools
* **Drawing Tools:** Rectangle (BBox), Circle, and Polygon selection.
* **Basemaps:** Standard OSM, Esri Satellite, and CartoDB Dark Matter.
* **Smart Clipping:** Auto-clips satellite imagery to circular selections for design use.

### 📥 Export Formats
* **Vectors (GIS):** Shapefile (.shp), GeoPackage (.gpkg), GeoJSON.
* **Design (Raster):** High-Res PNG, SVG (for Illustrator), PDF.
* **Robust Error Handling:** Automatically detects server timeouts or memory crashes and reports clear errors instead of silent failures.

---

## 📂 Project Structure

```text
/mapforge
├── main.py            # Backend logic (FastAPI)
├── index.html         # Frontend UI (Leaflet.js)
├── favicon.ico        # Browser Tab Icon
├── logo.png           # Project Logo
├── search.png         # Icon: Search Button
├── globe.png          # Icon: Global View Button
├── target.png         # Icon: Center Selection Button
├── requirements.txt   # Python Dependencies
└── temp/              # Temporary storage for generated maps (Auto-created)

🛠️ Installation & Setup

Clone the Repository:

Bash

git clone [https://github.com/DipankarKoushik/mapforge_osm_extractor.git](https://github.com/DipankarKoushik/mapforge_osm_extractor.git)
cd mapforge

Install Dependencies:

Bash

pip install -r requirements.txt

Run the Server:

Bash

uvicorn main:app --reload

Open in Browser: Go to http://127.0.0.1:8000


📝 License
This project uses data from OpenStreetMap (ODbL) and Esri World Imagery.