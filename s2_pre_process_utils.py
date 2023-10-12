import zipfile
from osgeo import gdal
import xml.etree.ElementTree as ET
import os
import sys
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio.mask import mask
from rasterio.windows import Window
from pathlib import Path
from glob import glob
import shutil
import uuid
import pyproj

class Utils(object):

    def gdal_error_handler(err_class, err_num, err_msg):
        errtype = {
                gdal.CE_None:'None',
                gdal.CE_Debug:'Debug',
                gdal.CE_Warning:'Warning',
                gdal.CE_Failure:'Failure',
                gdal.CE_Fatal:'Fatal'
        }
        err_msg = err_msg.replace('\n',' ')
        err_class = errtype.get(err_class, 'None')
        print('Error Number: %s' % (err_num))
        print('Error Type: %s' % (err_class))
        print('Error Message: %s' % (err_msg))


    def file_list_from_dir(directory, extension):
        file_list = glob(directory + extension)
        if len(file_list) == 0:
            print('## No ' + extension + ' files in input!')
            sys.exit()

        return file_list
    
    
    def is_valid_epsg(epsg_code):
        try:
            pyproj.CRS.from_epsg(epsg_code)
            return True
        except pyproj.exceptions.CRSError:
            return False
        

    def check_create_folder(directory):
        Path(directory).mkdir(exist_ok = True)


    def aoi_cloud_cover(inputProductPath, shape):

        scl_filename = Utils.extract_scl(inputProductPath)
        if scl_filename == None: return

        options = gdal.WarpOptions(cutlineDSName = shape, cropToCutline = True, dstSRS = 'EPSG:4326')
        Utils.open_option_warp_move(scl_filename, options, 'tmp/clip_scl.jp2')

        cloud_percentage = Utils.get_cloud_percentage(scl_filename)

        return cloud_percentage
    

    def get_cloud_percentage(scl_filename):

        scl_ds = rio.open(scl_filename).read(1)

        cloud_pixels = np.sum(np.isin(scl_ds, [8, 9]))    #8, 9 represents medium and high probability cloud classes in SRC
        total_data_pixels = scl_ds.size - np.sum(np.isin(scl_ds, [0]))

        scl_ds = None

        return (cloud_pixels / total_data_pixels) * 100

    
    def extract_scl(inputProductPath):
        with zipfile.ZipFile(inputProductPath, 'r') as zip_ref:
            scl_file = [f for f in zip_ref.namelist() if '_SCL_20m.jp2' in f]

            if scl_file == None: 
                return None

            scl_filename = 'tmp/' + os.path.basename(scl_file[0])

            with zip_ref.open(scl_file[0]) as source, open(scl_filename, 'wb') as target:
                target.write(source.read())
            return(scl_filename)


    def shape_to_geojson(output, shape):
        shp_file = gpd.read_file(shape)
        geojson = output + 'tmp.geojson'
        shp_file.to_file(geojson, driver='GeoJSON')
        return geojson
    

    def unzip_data_to_dir(data, tmp):
        unzipped_safe = tmp + str(uuid.uuid4())
        Path(unzipped_safe).mkdir(exist_ok = True)
        with zipfile.ZipFile(data, 'r') as zip_ref:
            zip_ref.extractall(unzipped_safe)
        
        return unzipped_safe
    

    def remove_folder(folder):
        shutil.rmtree(folder)
    
    
    def crs_warp(dataset, crs, output):
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)

        geotransform = gdal_dataset.GetGeoTransform()
        x_res = geotransform[1]
        y_res = -geotransform[5]

        src_SRS = gdal_dataset.GetProjection()

        options = gdal.WarpOptions(format = "GTiff", srcSRS = src_SRS, dstSRS = crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour)     
        gdal.Warp(output, gdal_dataset, options = options)
        shutil.move(output, dataset)
    
    
    def open_option_warp_move(dataset, options, output):
        gdal.UseExceptions()

        gdal_dataset = gdal.Open(dataset)
        gdal.Warp(output, gdal_dataset, options = options)
        shutil.move(output, dataset)
    

    # def clip_to_256(geotiff_path, shape, tmp_dir):

    #     gpd_shape = gpd.read_file(shape)
    #     geometries = list(gpd_shape.geometry)
    #     pad_width = 128

    #     with rio.open(geotiff_path, 'r+') as src:

    #         print(gpd_shape.crs)
    #         gpd_shape = gpd_shape.to_crs(src.crs)

    #         print(gpd_shape.crs)
    #         print(src.crs)
    #         sys.exit()
    #         # despite best efforts to match CRS og shp and raster, it continues to claim no overlap. CRS warp on raster fail

    #         buffer_clipped_rio, clipped_transform = mask(
    #             src, 
    #             geometries, 
    #             crop=True, 
    #             all_touched=True, 
    #             filled=False, 
    #             pad=True, 
    #             pad_width=pad_width,
    #             )
            
    #         buffer_clipped_rio = np.where(buffer_clipped_rio.mask, np.nan, buffer_clipped_rio)

    #         out_meta = src.meta
    #         out_meta.update({"driver": "GTiff",
    #              "height": buffer_clipped_rio.shape[1],
    #              "width": buffer_clipped_rio.shape[2],
    #              "transform": clipped_transform,
    #              "nodata": np.nan
    #              })

    #         with rio.open(tmp_dir + 'clipped_raster.tif', "w", **out_meta) as dest:
    #             dest.write(buffer_clipped_rio)

    #     with rio.open(tmp_dir + 'clipped_raster.tif') as src:

    #         new_width = (src.width // 256) * 256
    #         new_height = (src.height // 256) * 256

    #         window = Window(0, 0, new_width, new_height)
    #         clipped_data = src.read(window=window)
    #         new_transform = src.window_transform(window)

    #         with rio.open(tmp_dir + 'clipped_raster2.tif', 'w', 
    #                    driver='GTiff', 
    #                    height=new_height,
    #                    width=new_width, 
    #                    count=src.count,
    #                    dtype=str(clipped_data.dtype),
    #                    #crs=crs,
    #                    transform=new_transform
    #                    ) as dst:
    #             dst.write(clipped_data)

    #     shutil.move(tmp_dir + 'clipped_raster2.tif', geotiff_path)


    def remove_empty_files(geotiff, max_empty_percent):
        with rio.open(geotiff, 'r') as src:
            data = src.read(1)

        zero_pixel_count = (data == 0).sum()
        total_pixels = data.size
        percentage = (zero_pixel_count / total_pixels) * 100

        data = None

        if percentage >= max_empty_percent:
            print(f'# Removed {geotiff}, data coverage: {str(100 - percentage)} %')
            os.remove(geotiff)

