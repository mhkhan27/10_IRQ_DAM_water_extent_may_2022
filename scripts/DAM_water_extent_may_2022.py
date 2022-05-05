import os
import geopandas as gpd
import fiona
import pandas as pd
import glob
import openpyxl
import rasterio+
import numpy as np
from osgeo import gdal,  ogr, osr
import rasterio.features
from rasterio.features import shapes
import re
from shapely.geometry import shape

## read and reclassify image
img_path = r"inputs\GEE_output_img" ## change the path to the 'GEE_output_img' folder
file = glob.glob(img_path + "\\*.tif") # file list
dam_location = gpd.read_file(r"inputs\Data\Dam_poly_join.shp")
csv={}
for i in file:
    mask = None
    with rasterio.Env():
        with rasterio.open(i) as src:
            image = src.read(1) # first band
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v)
                in enumerate(
                shapes(image, mask=mask, transform=src.transform)))

    geoms = list(results)
    gpd_polygonized_raster = gpd.GeoDataFrame.from_features(geoms)
    water_poly = gpd_polygonized_raster[gpd_polygonized_raster.raster_val == 1]
    water_poly.crs = {"init": "epsg:4326"}
    water_poly = water_poly.to_crs(dam_location.crs)

    poly_with_dam_info = gpd.sjoin(dam_location, water_poly, how='right', op='intersects')
    poly_with_dam_info2 = poly_with_dam_info[~pd.isnull(poly_with_dam_info['Name'])]
    poly_with_dam_info2 = poly_with_dam_info2.dissolve(by='Name')
    poly_with_dam_info2 = poly_with_dam_info2.clip(dam_location)
    poly_with_dam_info2 = poly_with_dam_info2.to_crs(epsg=3891)
    poly_with_dam_info2["area"] = poly_with_dam_info2['geometry'].area / 10 ** 6
    year = re.findall('\d+', i )
    poly_with_dam_info2["Year"] = str(year)
    poly_with_dam_info2.to_file("outputs/water_poly/" +str(year)+".shp")
    csv[i] = pd.DataFrame(poly_with_dam_info2)

all_merge =pd.concat(csv.values(), ignore_index=True)
all_merge.to_excel(r'outputs/area/Dam_area.xlsx')

