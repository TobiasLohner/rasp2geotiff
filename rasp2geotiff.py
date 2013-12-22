#!/usr/bin/env python
import xcsoar
import osr
import gdal
import numpy as np
import os, sys
import math

idx_min_x = idx_max_x = idx_min_y = idx_max_y = 0
spa_x = spa_y = 0
lat_0 = lat_1 = lon_0 = 0
lat_c = lon_c = 0
raster_data = None

def get_parameters(line):
    global idx_min_x, idx_max_x, idx_min_y, idx_max_y, spa_x, spa_y, lat_0, lat_1, lon_0, lat_c, lon_c
    splitted = line.split(' ')

    i = 0
    while splitted[i] != 'Indexs=':
        i += 1

    idx_min_x = int(splitted[i + 1])
    idx_max_x = int(splitted[i + 2])
    idx_min_y = int(splitted[i + 3])
    idx_max_y = int(splitted[i + 4])

    i = 0
    while splitted[i] != 'Proj=':
        i += 1

    if splitted[i + 1] != 'lambert':
        print "Error - no lambert projection found..."
        return

    spa_x = float(splitted[i + 2])
    spa_y = float(splitted[i + 3])
    lat_0 = float(splitted[i + 4])
    lat_1 = float(splitted[i + 5])
    lon_0 = float(splitted[i + 6])
    lat_c = float(splitted[i + 7])
    lon_c = float(splitted[i + 8])

def read_data(line, idx):
    splitted = line.split(' ')
    
    if len(splitted) != idx_max_x - idx_min_x + 1:
        print "Error - grid resolution wrong?!?"
        return

    for i in range(len(splitted)):
        raster_data[(idx_max_y - idx_min_y) - idx - 1, i] = float(splitted[i])
        #raster_data[idx, i] = float(splitted[i])


i = 0
for line in open(sys.argv[1]):
    i += 1
    if line == '---':
        continue

    if line.startswith('Model='):
        get_parameters(line)
        raster_data = np.zeros((idx_max_x - idx_min_x + 1, idx_max_y - idx_min_y + 1), dtype=np.float32)

    if i >= 5:
        read_data(line, i - 5)


lcc = osr.SpatialReference()
lcc.ImportFromProj4("+proj=lcc +lat_1=" + str(lat_1) + " +lat_0=" + str(lat_0) + " +lon_0=" + str(lon_0) + " +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")

epsg4326 = osr.SpatialReference()
epsg4326.ImportFromEPSG(4326)

epsg4326_to_lcc = osr.CoordinateTransformation(epsg4326, lcc)

width = (idx_max_x - idx_min_x) + 1
height = (idx_max_y - idx_min_y) + 1

center_lcc = epsg4326_to_lcc.TransformPoint(lon_c, lat_c)
geotransform = [center_lcc[0] - width * spa_x / 2, spa_x, 0, center_lcc[1] + height * spa_y / 2, 0, -spa_y]


driver = gdal.GetDriverByName('GTiff')
dst_ds = driver.Create(sys.argv[1] + ".tiff", width, height, 1, gdal.GDT_Float32)
dst_ds.SetProjection(lcc.ExportToWkt())
dst_ds.SetGeoTransform(geotransform)
dst_ds.GetRasterBand(1).WriteArray(raster_data)
dst_ds = None

