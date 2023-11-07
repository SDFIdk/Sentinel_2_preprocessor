import os
import sys

from s2_pre_process_preprocessing import Preprocessor

if __name__== '__main__':

    ### ----------------------------------- ########### ----------------------------------- ###
    ### ----------------------------------- USER INPUTS ----------------------------------- ###
    ### ----------------------------------- ########### ----------------------------------- ###

    # input_dir = 'input/'
    input_dir = "D:/s2_ribe/"
    output_dir = 'output/'
    # input/output will be created if not present

    shape = 'ribe_aoi/ribe_aoi.shp'
    # path to .shp file in unzipped shape dir

    crs = 'EPSG:25832'
    # CRS in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid 

    date_range = ('20200201', '20200501')
    # Tuple with date strings in DDMMYYYY format

    max_cloud_pct = 60  #max allowed cloud pct in aoi
    # Note this range extends to whole raster, not shape extent

    preprocessor = Preprocessor(input_dir, output_dir)

    preprocessor.self_check(crs)

    preprocessor.s2_safe_to_geotiff(shape, max_cloud_pct)

    preprocessor.warp_files_to_crs(crs)  

    preprocessor.clip_to_shape(shape, crs)      

    preprocessor.warp_files_to_crs(crs)       

    preprocessor.remove_empty_files(max_empty_percent = 95)