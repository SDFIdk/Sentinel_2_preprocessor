This script takes unprocessed Sentinel-2 SAFE files and converts them to geoTiff, cut down to the extent of a shapefile provided by the user. 

Script takes:
Input: Path to dir with SAFE files

Output: Path to output geotiff

Shape: Path to .shp. file. If none, no clipping will be made

Max_cloud_pct: Maximum allowed clouds in area defined by shape (or image of on shape)

Max_empty: Max allowed no_data pct. of outputs
