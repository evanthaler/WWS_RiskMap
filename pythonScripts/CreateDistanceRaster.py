import geopandas as gpd
import rasterio
from rasterio import features, transform
import numpy as np
from scipy.ndimage import distance_transform_edt

# 1. Load and project data
gdf = gpd.read_file("/Users/evanthaler/Documents/GitHub/WWS_RiskMap/data/source_waters/pnw-intake-points.gpkg").to_crs('epsg:5070')

# 2. Define the grid resolution (500m)
pixel_size = 100
minx, miny, maxx, maxy = gdf.total_bounds
width = int((maxx - minx) / pixel_size)
height = int((maxy - miny) / pixel_size)
out_transform = transform.from_origin(minx, maxy, pixel_size, pixel_size)

# 3. Rasterize: Create a binary mask (1 at points, 0 elsewhere)
# Shapes must be a list of (geometry, value)
shapes = ((geom, 1) for geom in gdf.geometry)
mask = features.rasterize(
    shapes, 
    out_shape=(height, width), 
    transform=out_transform, 
    fill=0, 
    dtype=np.uint8
)

# 4. Calculate Distance Transform
# We invert the mask because edt calculates distance to the nearest 0
# So we pass (mask == 0) to get distance to the nearest 1 (our points)
dist_array = distance_transform_edt(mask == 0) * pixel_size

# 5. Export to GeoTIFF
with rasterio.open(
    "/Users/evanthaler/Documents/GitHub/WWS_RiskMap/data/source_waters/distance_to_points.tif",
    'w', driver='GTiff', height=height, width=width, count=1,
    dtype=dist_array.dtype, crs='epsg:5070', transform=out_transform
) as dst:
    dst.write(dist_array, 1)