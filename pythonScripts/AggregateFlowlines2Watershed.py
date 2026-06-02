import geopandas as gpd
import os,glob
import numpy as np
import pandas as pd

# ---- USER INPUT ----
polygon_dir = "/Users/evanthaler/Documents/GitHub/WWS_RiskMap/data/source_waters/indivSourceWaters"  # Directory of HUC12 GPKG files
points_gpkg = "/Users/evanthaler/Documents/Projects/OSU/EPARiskMapping/datasets/IndexVariablesDatasets/Flowlines/FlowlinesStreamCatVars_landslides_IDF_WHP_peakFlows_IWI.gpkg"  # StreamCat variables GeoPackage
point_layer = os.path.basename(points_gpkg);point_layer=os.path.splitext(point_layer)[0]  # Layer name in point GPKG
outdir = "/Users/evanthaler/Documents/GitHub/WWS_RiskMap/data/source_waters/FlowAttributesSourceWaters"
outmerge = f"{outdir}/SourceAreasAggregate.gpkg"  
value_fields = ['Precip_1hr_100yr',
                  "bfiws",
                  "iwi",
                  "MaximumPeakFlow",                   
                  "pct_wetland",
                  "rckdepws",
                  "permws",
                  "runoffcat",
                  'LandslideSus',
                  'ConditionalFlameLength',
                  'BurnPotential',
                  'omws']
statistics = ["sum","median",'max']  # Stats to compute
#statistics = ['mean',"median"]
#weight_field = "shape_length"  # Field to use for weighting
output_suffix = "_SourceAreas"  # Suffix for output files
weight_field = 'SHAPE_LENG'

# ---- LOAD POINT DATA ----
points = gpd.read_file(points_gpkg)
points = points.to_crs(epsg=4326)

# Ensure weight_field is numeric
points[weight_field] = pd.to_numeric(points[weight_field], errors="coerce")

# ---- PROCESS POLYGON FILES ----
for file in os.listdir(polygon_dir):
    if file.endswith(".gpkg"):
        poly_path = os.path.join(polygon_dir, file)
        poly_gdf = gpd.read_file(poly_path)
        poly_gdf = poly_gdf.to_crs(points.crs)

        # Initialize dictionary to collect results
        stat_results = {
            f"{stat}_{field}": [] for field in value_fields for stat in statistics
        }

        for poly in poly_gdf.geometry:
            pts = points[points.geometry.within(poly)]

            for field in value_fields:
                vals = pts[field] if not pts.empty else pd.Series(dtype=float)
                weights = pts[weight_field] if not pts.empty else pd.Series(dtype=float)

                for stat in statistics:
                    key = f"{stat}_{field}"

                    if not pts.empty and not vals.isna().all():
                        if stat == "mean":
                            # Calculate weighted mean using shape_length
                            valid = ~vals.isna() & ~weights.isna()
                            if valid.any():
                                weighted_vals = vals[valid]
                                weighted_weights = weights[valid]
                                try:
                                    if weighted_weights.sum() == 0:
                                        # Fall back to unweighted mean
                                        mean_value = np.nanmean(weighted_vals)
                                    else:
                                        mean_value = np.average(weighted_vals, weights=weighted_weights)
                                    stat_results[key].append(mean_value)
                                except ZeroDivisionError:
                                    # Fall back to unweighted mean if weird edge case
                                    stat_results[key].append(np.nanmean(weighted_vals))
                            else:
                                stat_results[key].append(None)
                        elif stat == "sum":
                            stat_results[key].append(np.nansum(vals))
                        elif stat == "median":
                            stat_results[key].append(np.nanmedian(vals))
                        elif stat == "max":
                            stat_results[key].append(np.nanmax(vals))
                        else:
                            raise ValueError(f"Unsupported statistic: {stat}")
                    else:
                        stat_results[key].append(None)

        # Add results to GeoDataFrame
        for col, values in stat_results.items():
            poly_gdf[col] = values

        # Save output

        out_path = os.path.join(outdir, file.replace(".gpkg", f"{output_suffix}.gpkg"))
        poly_gdf.to_file(out_path, driver="GPKG")
        print(f"Saved: {out_path}")
huc12_list = glob.glob(outdir+'/*.gpkg')



empty_gdf = gpd.GeoDataFrame()   
for huc in huc12_list:
    gdf = gpd.read_file(huc)
    gdf_huc12 = np.array(gdf.PWSID)
    empty_gdf = pd.concat([empty_gdf,gdf])
    empty_gdf.to_crs(gdf.crs)
# empty_gdf=empty_gdf[~np.isnan(empty_gdf.mean_WWFI_mean)]
# empty_gdf['Wildfire_rescale'] = empty_gdf.mean_Wildfire/np.max(empty_gdf.mean_Wildfire)*100
# empty_gdf['Watershed_rescale'] = empty_gdf.mean_Watershed/np.max(empty_gdf.mean_Watershed)*100
# empty_gdf['Biological_rescale'] = empty_gdf.mean_Biological/np.max(empty_gdf.mean_Biological)*100
# empty_gdf['WWFI_rescale'] = empty_gdf.mean_WWFI_mean/np.max(empty_gdf.mean_WWFI_mean)*100
empty_gdf.to_file(outmerge,driver='GPKG')