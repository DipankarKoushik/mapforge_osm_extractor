MapForge (Geospatial Extraction Engine)



A professional full-stack web application to extract, visualize, and export high-precision urban data from OpenStreetMap (OSM) for any location on Earth.



[Status](https://img.shields.io/badge/Status-Production-success)

[Python](https://img.shields.io/badge/Python-3.10+-blue)

[FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)

[Leaflet](https://img.shields.io/badge/Frontend-Leaflet.js-orange)



🚀 Try here

[Click here to view the Live App](https://osmextractor-mapforge.onrender.com/)



Key Features \& Recent Updates

* Modern UI/UX
* Auto-Dark Mode
* Mobile Responsive



Advanced Mapping Tools

* Dual Search Engine: Search by City Name or precise Coordinates.
* Basemaps: Switch between Standard Street, Satellite (Esri World Imagery), and Dark Mode (CartoDB).



Select your area of interest using:

&nbsp;   🟦 Rectangle (Bounding Box)\*\*

&nbsp;   ⚪ Circle (Radius Select)

&nbsp;   ✍️ Freehand Polygon



Data Export \& Visualization



* Download specific urban layers: Buildings, Streets, Water, Parks, Schools, Medical, Railways, Power Lines.
* GIS Vector Support: Export data as Shapefile (.shp), GeoPackage (.gpkg), or GeoJSON for professional GIS software (QGIS/ArcGIS).
* Graphic Design Export: Get high-resolution SVG, PDF, or PNG maps.



Smart Clipping (Advanced)

* Circular Cutouts: When exporting a circular selection as an image (PNG/SVG), the engine applies a mathematical clipping mask, removing the square corners and creating a transparent background perfect for design layouts.





Tech Stack:

* Backend
* Python 3.10+
* FastAPI: High-performance API framework.
* OSMnx: For retrieving and constructing street networks.
* GeoPandas \& Shapely: For geometric manipulation and coordinate projection (EPSG:4326 ↔ EPSG:3857).
* Contextily: For fetching and stitching satellite map tiles.
* Matplotlib: For generating static map images and applying clipping masks.



Frontend

* HTML5 / CSS3: Custom responsive layout with CSS Variables for theming.
* Leaflet.js: Interactive map interface.
* Leaflet-Draw: Vector drawing tools.





Local Installation Guide

1\. Clone the Repository

git clone https://github.com/YOUR\_USERNAME/osm-urban-planner.git

cd osm-urban-planner



2\. Create Virtual Environment

* Windows

python -m venv venv

.\\venv\\Scripts\\activate



* Mac/Linux

python3 -m venv venv

source venv/bin/activate



3\. Install Dependencies

pip install -r requirements.txt



4\. Run the Server

uvicorn main:app --reload



5\. Access the App

Open your browser and go to: http://127.0.0.1:8000



License \& Credits

* Map Data © OpenStreetMap contributors.
* Satellite Imagery © Esri.
* Built using OSMnx by Geoff Boeing.
