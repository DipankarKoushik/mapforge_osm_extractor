from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
import osmnx as ox
import uuid
import os
import shutil
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon
import json

app = FastAPI()

os.makedirs("temp", exist_ok=True)
plt.switch_backend('Agg')

# --- CONFIGURATION ---
LAYER_CONFIG = {
    "water": {"tags": {"natural": "water", "waterway": ["river", "canal", "stream"]}, "color": "#aed9e0", "geom": ["Polygon", "MultiPolygon"], "order": 1},
    "parks": {"tags": {"leisure": "park", "landuse": ["grass", "forest", "recreation_ground"]}, "color": "#c7e9c0", "geom": ["Polygon", "MultiPolygon"], "order": 2},
    "schools": {"tags": {"amenity": ["school", "university"]}, "color": "#fdd0a2", "geom": ["Polygon", "MultiPolygon"], "order": 3},
    "medical": {"tags": {"amenity": "hospital"}, "color": "#fbb4b9", "geom": ["Polygon", "MultiPolygon"], "order": 3},
    "buildings": {"tags": {"building": True}, "color": "#525252", "geom": ["Polygon", "MultiPolygon"], "order": 4},
    "railways": {"tags": {"railway": True}, "color": "#54278f", "geom": ["LineString", "MultiLineString"], "order": 5},
    "streets": {"tags": {}, "color": "#000000", "geom": ["LineString", "MultiLineString"], "order": 6},
    "power": {"tags": {"power": "line"}, "color": "#f1c40f", "geom": ["LineString", "MultiLineString"], "order": 7}
}

def clean_gdf(gdf, layer_name):
    if gdf.empty: return gdf
    gdf = gdf.fillna('')
    for col in gdf.columns:
        if col != 'geometry':
            gdf[col] = gdf[col].astype(str)
    allowed = LAYER_CONFIG.get(layer_name, {}).get("geom")
    if allowed:
        gdf = gdf[gdf.geometry.type.isin(allowed)]
    return gdf

def fetch_data(layer, bbox=None, center=None, polygon=None):
    """
    Fetches data using BBox, Point (Circle), or Polygon.
    """
    try:
        if layer == "streets":
            if polygon:
                G = ox.graph_from_polygon(polygon, network_type='all')
            elif bbox:
                G = ox.graph_from_bbox(bbox=bbox, network_type='all')
            else:
                G = ox.graph_from_point((center[0], center[1]), dist=center[2], network_type='all')
            _, gdf = ox.graph_to_gdfs(G)
        else:
            tags = LAYER_CONFIG.get(layer, {}).get("tags")
            if polygon:
                gdf = ox.features_from_polygon(polygon, tags=tags)
            elif bbox:
                gdf = ox.features_from_bbox(bbox=bbox, tags=tags)
            else:
                gdf = ox.features_from_point((center[0], center[1]), tags=tags, dist=center[2])
        
        return clean_gdf(gdf, layer)
    except Exception as e:
        # print(f"Layer {layer} failed: {e}") 
        return pd.DataFrame()

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

@app.get("/logo.png")
async def get_logo():
    # This checks if the file exists and serves it
    if os.path.exists("logo.png"):
        return FileResponse("logo.png")
    return {"error": "File not found"}

@app.get("/")
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/download")
async def download_multilayers(
    layers: str, 
    type: str, 
    fmt: str = "geojson",
    # Geometry Params
    north: float = 0, south: float = 0, east: float = 0, west: float = 0, # BBox
    lat: float = 0, lon: float = 0, radius: float = 0, # Circle
    poly_coords: str = None # Polygon (JSON string of points)
):
    selected_layers = layers.split(",")
    selected_layers.sort(key=lambda x: LAYER_CONFIG.get(x, {}).get("order", 99))
    unique_id = uuid.uuid4().hex[:6]
    
    # 1. Prepare Polygon Object if needed
    polygon_geom = None
    if type == "polygon" and poly_coords:
        # Convert JSON string "[[lat,lon], ...]" to list of tuples
        coords_list = json.loads(poly_coords)
        # Shapely expects (lon, lat) order, but Leaflet gives (lat, lon). We must swap them.
        # coords_list from frontend: [[lat, lon], [lat, lon]]
        # Shapely needs: [(lon, lat), (lon, lat)]
        shapely_coords = [(pt[1], pt[0]) for pt in coords_list]
        polygon_geom = Polygon(shapely_coords)

    # 2. Fetch Data
    data_store = {}
    print(f"Fetching {len(selected_layers)} layers (Type: {type})...")
    
    for layer in selected_layers:
        if type == "bbox":
            gdf = fetch_data(layer, bbox=(north, south, east, west))
        elif type == "circle":
            gdf = fetch_data(layer, center=(lat, lon, radius))
        elif type == "polygon":
            gdf = fetch_data(layer, polygon=polygon_geom)
            
        if not gdf.empty:
            data_store[layer] = gdf

    if not data_store:
        raise HTTPException(404, detail="No data found. Try a larger area or different location.")

    # 3. Save Logic (Image vs Data)
    if fmt in ['svg', 'png']:
        filename = f"map_{unique_id}.{fmt}"
        filepath = os.path.join("temp", filename)
        fig, ax = plt.subplots(figsize=(10, 10))
        
        for layer, gdf in data_store.items():
            color = LAYER_CONFIG.get(layer, {}).get("color", "black")
            if layer in ['streets', 'railways', 'power']:
                gdf.plot(ax=ax, linewidth=0.8, edgecolor=color)
            else:
                gdf.plot(ax=ax, facecolor=color, edgecolor='none')

        ax.set_axis_off()
        ax.margins(0)
        plt.savefig(filepath, dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close(fig)
        return FileResponse(filepath, filename=filename, media_type=f"image/{fmt}")

    else:
        folder_name = f"export_{unique_id}"
        folder_path = os.path.join("temp", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        for layer, gdf in data_store.items():
            if fmt == "shp":
                shp_dir = os.path.join(folder_path, layer)
                os.makedirs(shp_dir, exist_ok=True)
                gdf.to_file(os.path.join(shp_dir, f"{layer}.shp"), driver="ESRI Shapefile")
            elif fmt == "gpkg":
                gdf.to_file(os.path.join(folder_path, f"{layer}.gpkg"), driver="GPKG")
            else:
                gdf.to_file(os.path.join(folder_path, f"{layer}.geojson"), driver="GeoJSON")
        
        shutil.make_archive(folder_path, 'zip', folder_path)
        return FileResponse(f"{folder_path}.zip", filename=f"osm_extract_{unique_id}.zip", media_type="application/zip")