import geopandas as gpd
import os


# 1. FILE PATHS

gpkg_path = r"wijkenbuurten_2025_v1.gpkg"

output_dir = r"\Data"
os.makedirs(output_dir, exist_ok=True)


# 2. LOAD MUNICIPALITIES

gemeenten = gpd.read_file(gpkg_path, layer="gemeenten")

print("Loaded municipalities:", gemeenten.shape)


# 3. FILTER AMSTERDAM

amsterdam = gemeenten[gemeenten["gemeentenaam"] == "Amsterdam"].copy()

print("Amsterdam loaded:", amsterdam.shape)

# remove invalid population rows (if present)
if "aantal_inwoners" in amsterdam.columns:
    amsterdam = amsterdam[amsterdam["aantal_inwoners"] != -99997]

print("Amsterdam cleaned:", amsterdam.shape)


# 4. SAVE AMSTERDAM BOUNDARY (FIXED GPKG WRITE)

amsterdam_path = os.path.join(output_dir, "amsterdam_boundary.gpkg")

amsterdam.to_file(
    amsterdam_path,
    layer="amsterdam_boundary",
    driver="GPKG"
)

print("Amsterdam boundary saved:", amsterdam_path)


# 5. LOAD ROAD NETWORK

roads_path = r"nwb_wegen (1).gpkg"

gdf_wegvakken = gpd.read_file(roads_path, layer="wegvakken")
gdf_hectopunten = gpd.read_file(roads_path, layer="hectopunten")


# 6. ENSURE SAME CRS

gdf_wegvakken = gdf_wegvakken.to_crs(amsterdam.crs)
gdf_hectopunten = gdf_hectopunten.to_crs(amsterdam.crs)


# 7. CLIP TO AMSTERDAM

from geopandas import clip

wegvakken_amsterdam = gpd.clip(gdf_wegvakken, amsterdam)
hectopunten_amsterdam = gpd.clip(gdf_hectopunten, amsterdam)


# 8. SAVE CLIPPED DATASETS

wegvakken_path = os.path.join(output_dir, "wegvakken_amsterdam.gpkg")
hectopunten_path = os.path.join(output_dir, "hectopunten_amsterdam.gpkg")

wegvakken_amsterdam.to_file(
    wegvakken_path,
    layer="wegvakken_amsterdam",
    driver="GPKG"
)

hectopunten_amsterdam.to_file(
    hectopunten_path,
    layer="hectopunten_amsterdam",
    driver="GPKG"
)

print("Clipping complete")
print("Roads saved:", wegvakken_path)
print("Points saved:", hectopunten_path)


# 9. FINAL CHECK

print("\nFINAL CHECKS")
print("CRS:", amsterdam.crs)
print("Bounds:", amsterdam.total_bounds)
print("Geometry type:", amsterdam.geometry.iloc[0].geom_type)