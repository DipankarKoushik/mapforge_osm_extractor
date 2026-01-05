from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
import osmnx as ox
import uuid
import os
import shutil
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon as MplPolygon
import pandas as pd
from shapely.geometry import Polygon, box, Point
import json
import contextily as cx 
import geopandas as gpd

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

# --- HELPER FUNCTIONS ---
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
    try:
        if layer == "streets":
            if polygon: G = ox.graph_from_polygon(polygon, network_type='all')
            elif bbox: G = ox.graph_from_bbox(bbox=bbox, network_type='all')
            else: G = ox.graph_from_point((center[0], center[1]), dist=center[2], network_type='all')
            _, gdf = ox.graph_to_gdfs(G)
        else:
            tags = LAYER_CONFIG.get(layer, {}).get("tags")
            if polygon: gdf = ox.features_from_polygon(polygon, tags=tags)
            elif bbox: gdf = ox.features_from_bbox(bbox=bbox, tags=tags)
            else: gdf = ox.features_from_point((center[0], center[1]), tags=tags, dist=center[2])
        return clean_gdf(gdf, layer)
    except Exception:
        return pd.DataFrame()

# --- STATIC FILES ---
@app.get("/logo.png")
async def get_logo():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    return FileResponse(path) if os.path.exists(path) else {"error": "Logo not found"}

@app.get("/favicon.ico")
async def get_favicon():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
    return FileResponse(path) if os.path.exists(path) else {"error": "No favicon"}

@app.get("/")
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/download")
async def download_multilayers(
    layers: str = "", type: str = "bbox", fmt: str = "geojson",
    north: float = 0, south: float = 0, east: float = 0, west: float = 0,
    lat: float = 0, lon: float = 0, radius: float = 0, poly_coords: str = None,
    basemap: bool = False,
    basemap_style: str = "osm"
):
    selected_layers = [l for l in layers.split(",") if l]
    selected_layers.sort(key=lambda x: LAYER_CONFIG.get(x, {}).get("order", 99))
    unique_id = uuid.uuid4().hex[:6]
    
    # 1. Define View Geometry
    target_geometry = None
    if type == "polygon" and poly_coords:
        coords_list = json.loads(poly_coords)
        shapely_coords = [(pt[1], pt[0]) for pt in coords_list]
        target_geometry = Polygon(shapely_coords)
    elif type == "bbox":
        target_geometry = box(west, south, east, north)
    elif type == "circle":
        deg_radius = radius / 111000 
        target_geometry = Point(lon, lat).buffer(deg_radius)

    # 2. Fetch Data
    data_store = {}
    if selected_layers:
        for layer in selected_layers:
            if type == "bbox": gdf = fetch_data(layer, bbox=(north, south, east, west))
            elif type == "circle": gdf = fetch_data(layer, center=(lat, lon, radius))
            elif type == "polygon": gdf = fetch_data(layer, polygon=target_geometry)
            if not gdf.empty: data_store[layer] = gdf

    if not data_store and not basemap:
        raise HTTPException(404, detail="No data found.")

    # 3. EXPORT LOGIC (PNG/SVG/PDF)
    if fmt in ['svg', 'png', 'pdf']:
        filename = f"map_{unique_id}.{fmt}"
        filepath = os.path.join("temp", filename)
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Lock Camera to Exact Area
        view_gdf = gpd.GeoDataFrame({'geometry': [target_geometry]}, crs="EPSG:4326")
        view_gdf = view_gdf.to_crs(epsg=3857)
        minx, miny, maxx, maxy = view_gdf.total_bounds
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)

        # Plot Data Layers
        for layer, gdf in data_store.items():
            if gdf.crs != "EPSG:3857": gdf = gdf.to_crs(epsg=3857)
            color = LAYER_CONFIG.get(layer, {}).get("color", "black")
            if layer in ['streets', 'railways', 'power']:
                gdf.plot(ax=ax, linewidth=0.8, edgecolor=color)
            else:
                gdf.plot(ax=ax, facecolor=color, edgecolor='none', alpha=0.7)

        # Add Basemap
        if basemap:
            try:
                provider = cx.providers.OpenStreetMap.Mapnik
                if basemap_style == "satellite": provider = cx.providers.Esri.WorldImagery
                elif basemap_style == "dark": provider = cx.providers.CartoDB.DarkMatter
                cx.add_basemap(ax, crs="EPSG:3857", source=provider)
            except Exception as e:
                print(f"Basemap error: {e}")

        # --- FINAL CLIP LOGIC ---
        if type == "circle":
            # 1. Calculate center in Web Mercator
            center_point = gpd.points_from_xy([lon], [lat], crs="EPSG:4326").to_crs("EPSG:3857")[0]
            
            # 2. Create an INVISIBLE Circle Patch
            # facecolor='none' removes the blue fill
            # edgecolor='none' removes the black border
            clip_patch = Circle(
                (center_point.x, center_point.y), radius, 
                transform=ax.transData, 
                facecolor='none', edgecolor='none' 
            )
            ax.add_patch(clip_patch)
            
            # 3. Apply this patch as a "Cookie Cutter" to EVERYTHING
            # Cut the Basemap Image
            for img in ax.images:
                img.set_clip_path(clip_patch)
            # Cut the Vector Layers (Streets, Buildings)
            for collection in ax.collections:
                collection.set_clip_path(clip_patch)
            # Cut Lines (if any remain)
            for line in ax.lines:
                line.set_clip_path(clip_patch)

        ax.set_axis_off()
        ax.margins(0)
        plt.savefig(filepath, dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close(fig)
        return FileResponse(filepath, filename=filename, media_type=f"image/{fmt}")

    # 4. Vector Export (Unchanged)
    else:
        folder_name = f"export_{unique_id}"
        folder_path = os.path.join("temp", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        if not data_store:
             raise HTTPException(400, detail="Cannot export Basemap-only as Vector.")

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