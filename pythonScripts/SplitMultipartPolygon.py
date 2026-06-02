import geopandas as gpd
import os

# Read input GeoPackage
gdf = gpd.read_file("/Users/evanthaler/Documents/GitHub/WWS_RiskMap/data/source_waters/pnw-dwsa-with-intakes.gpkg")

# Explode multipart geometries
gdf_single = gdf.explode(index_parts=True)

# Reset index
gdf_single = gdf_single.reset_index(drop=True)

# Output directory
outdir = "/Users/evanthaler/Documents/GitHub/WWS_RiskMap/data/source_waters/indivSourceWaters"
os.makedirs(outdir, exist_ok=True)

# Write each feature to its own GeoPackage
for i, row in gdf_single.iterrows():
    out_gdf = gpd.GeoDataFrame(
        [row],
        columns=gdf_single.columns,
        crs=gdf_single.crs
    )

    out_gdf.to_file(
        os.path.join(outdir, f"feature_{i+1}.gpkg"),
        driver="GPKG"
    )