#!/usr/bin/env python
"""
The imageutils module contains general utilities for applying to images.
"""
# Maintain python 2 backwards compatibility
from __future__ import print_function
# import the C++ extension into this level
from ._imageutils import *
import rsgislib 

import os
import math
import shutil

import numpy

import osgeo.gdal as gdal
import osgeo.osr as osr

from rios import applier

gdal.UseExceptions()


class OutImageInfo(object):
    """
A class which is used to define the information to create a new output image.
This class is used within the StdImgBlockIter class.

:param file_name: is the output image file name and path.
:param name: is a name associated with this layer - doesn't really matter what you use but needs to be unique; this is used as a dict key in some functions.
:param nbands: is an int with the number of output image bands.
:param no_data_val: is a no data value for the output image
:param gdalformat: is the output image file format
:param datatype: is the output datatype rsgislib.TYPE_*

"""
    def __init__(self, file_name=None, name=None, nbands=None, no_data_val=None, gdalformat=None, datatype=None):
        """
        :param file_name: is the input image file name and path.
        :param name: is a name associated with this layer - doesn't really matter what you use but needs to be unique; this is used as a dict key in some functions.
        :param nbands: is an int with the number of output image bands.
        :param no_data_val: is a no data value for the output image
        :param gdalformat: is the output image file format
        :param datatype: is the output datatype rsgislib.TYPE_*
        """
        self.file_name = file_name
        self.name = name
        self.nbands = nbands
        self.no_data_val = no_data_val
        self.gdalformat = gdalformat
        self.datatype = datatype


class SharpBandInfo(object):
    """
Create a list of these objects to pass to the sharpenLowResBands function.

:param band: is the band number (band numbering starts at 1).
:param status: needs to be either rsgislib.SHARP_RES_IGNORE, rsgislib.SHARP_RES_LOW or rsgislib.SHARP_RES_HIGH
               lowres bands will be sharpened using the highres bands and ignored bands
               will just be copied into the output image.
:param name: is a name associated with this image band - doesn't really matter what you put in here.

"""
    def __init__(self, band=None, status=None, name=None):
        """
        :param band: is the band number (band numbering starts at 1).
        :param status: needs to be either 'ignore', 'lowres' or 'highres' - lowres bands will be sharpened using the highres bands and ignored bands will just be copied into the output image.
        :param name: is a name associated with this image band - doesn't really matter what you put in here.

        """
        self.band = band
        self.status = status
        self.name = name

# Define Class for time series fill
class RSGISTimeseriesFillInfo(object):
    """
Create a list of these objects to pass to the fillTimeSeriesGaps function

:param year: year the composite represents.
:param day: the (nominal) day within the year the composite represents (a value of zero and day will not be used)
:param compImg: The input compsite image which has been generated.
:param imgRef:  The reference layer (e.g., from createMaxNDVIComposite or createMaxNDVINDWICompositeLandsat) with zero for no data regions
:param outRef: A boolean variable specify which layer a fill reference layer is to be produced.

"""
    def __init__(self, year=1900, day=0, compImg=None, imgRef=None, outRef=False):
        """
        :param year: year the composite represents.
        :param day: the (nominal) day within the year the composite represents (a value of zero and day will not be used)
        :param compImg: The input compsite image which has been generated.
        :param imgRef:  The reference layer (e.g., from createMaxNDVIComposite or createMaxNDVINDWICompositeLandsat) with zero for no data regions
        :param outRef: A boolean variable specify which layer a fill reference layer is to be produced.

        """
        self.year = year
        self.day = day
        self.compImg = compImg
        self.imgRef = imgRef
        self.outRef = outRef
    
    def __repr__(self):
        return repr((self.year, self.day, self.compImg, self.imgRef, self.outRef))

def set_env_vars_lzw_gtiff_outs(bigtiff=True):
    """
    Set environmental variables such that outputted
    GeoTIFF files are outputted as tiled and compressed.

    :param bigtiff: If True GTIFF files will be outputted
                    in big tiff format.

    """
    if bigtiff:
        os.environ["RSGISLIB_IMG_CRT_OPTS_GTIFF"] = "TILED=YES:COMPRESS=LZW:BIGTIFF=YES"
    else:
        os.environ["RSGISLIB_IMG_CRT_OPTS_GTIFF"] = "TILED=YES:COMPRESS=LZW"

def get_rsgislib_datatype_from_img(input_img):
    """
    Returns the rsgislib datatype ENUM (e.g., rsgislib.TYPE_8INT)
    for the inputted raster file

    :return: int

    """
    raster = gdal.Open(input_img, gdal.GA_ReadOnly)
    if raster == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    band = raster.GetRasterBand(1)
    if band == None:
        raise rsgislib.RSGISPyException('Could not open raster band 1 in image: \'' + input_img + '\'')
    gdal_dtype = gdal.GetDataTypeName(band.DataType)
    raster = None
    return rsgislib.get_rsgislib_datatype(gdal_dtype)

def get_gdal_datatype_from_img(input_img):
    """
    Returns the GDAL datatype ENUM (e.g., GDT_Float32) for the inputted raster file.

    :return: ints

    """
    raster = gdal.Open(input_img, gdal.GA_ReadOnly)
    if raster == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    band = raster.GetRasterBand(1)
    if band == None:
        raise rsgislib.RSGISPyException('Could not open raster band 1 in image: \'' + input_img + '\'')
    gdal_dtype = band.DataType
    raster = None
    return gdal_dtype

def get_gdal_datatype_name_from_img(input_img):
    """
    Returns the GDAL datatype ENUM (e.g., GDT_Float32) for the inputted raster file.

    :return: int

    """
    raster = gdal.Open(input_img, gdal.GA_ReadOnly)
    if raster == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    band = raster.GetRasterBand(1)
    if band == None:
        raise rsgislib.RSGISPyException('Could not open raster band 1 in image: \'' + input_img + '\'')
    dtypeName = gdal.GetDataTypeName(band.DataType)
    raster = None
    return dtypeName


def get_file_img_extension(gdalformat:str):
    """
    A function to get the extension for a given file format
    (NOTE, currently only KEA, GTIFF, HFA, PCI and ENVI are supported).

    :return: string

    """
    ext = ".NA"
    if gdalformat.lower() == "kea":
        ext = "kea"
    elif gdalformat.lower() == "gtiff":
        ext = "tif"
    elif gdalformat.lower() == "hfa":
        ext = "img"
    elif gdalformat.lower() == "envi":
        ext = "env"
    elif gdalformat.lower() == "pcidsk":
        ext = "pix"
    else:
        raise rsgislib.RSGISPyException(
            "The extension for the gdalformat specified is unknown."
        )
    return ext


def get_gdal_format_from_ext(input_file:str):
    """
    Get GDAL format, based on input_file

    :return: string

    """
    gdalStr = ""
    extension = os.path.splitext(input_file)[-1]
    if extension == ".env":
        gdalStr = "ENVI"
    elif extension == ".kea":
        gdalStr = "KEA"
    elif extension == ".tif" or extension == ".tiff":
        gdalStr = "GTiff"
    elif extension == ".img":
        gdalStr = "HFA"
    elif extension == ".pix":
        gdalStr = "PCIDSK"
    else:
        raise rsgislib.RSGISPyException("Type not recognised")
    return gdalStr


def rename_gdal_layer(input_img, output_img):
    """
    Rename all the files associated with a GDAL layer.

    :param input_img: The current name of the GDAL layer.
    :param output_img: The output name of the GDAL layer.

    """
    layerDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    gdalDriver = layerDS.GetDriver()
    layerDS = None
    gdalDriver.Rename(output_img, input_img)

def get_image_res(input_img, abs_vals=False):
    """
    A function to retrieve the image resolution.

    :param input_img: input image file
    :param abs_vals: if True then returned x/y values will be positive (default: False)

    :return: xRes, yRes

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException("Could not open raster image: {}".format(input_img))

    geotransform = rasterDS.GetGeoTransform()
    xRes = geotransform[1]
    yRes = geotransform[5]
    if abs_vals:
        yRes = abs(yRes)
        xRes = abs(xRes)
    rasterDS = None
    return xRes, yRes

def do_image_res_match(in_a_img, in_b_img):
    """
    A function to test whether two images have the same
    image pixel resolution.

    :return: boolean

    """
    img1XRes, img1YRes = get_image_res(in_a_img)
    img2XRes, img2YRes = get_image_res(in_b_img)

    return ((img1XRes == img2XRes) and (img1YRes == img2YRes))

def get_image_size(input_img):
    """
    A function to retrieve the image size in pixels.

    :return: xSize, ySize

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')

    xSize = rasterDS.RasterXSize
    ySize = rasterDS.RasterYSize
    rasterDS = None
    return xSize, ySize

def get_image_bbox(input_img):
    """
    A function to retrieve the bounding box in the spatial
    coordinates of the image.

    :return: (MinX, MaxX, MinY, MaxY)

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')

    xSize = rasterDS.RasterXSize
    ySize = rasterDS.RasterYSize

    geotransform = rasterDS.GetGeoTransform()
    tlX = geotransform[0]
    tlY = geotransform[3]
    xRes = geotransform[1]
    yRes = geotransform[5]
    if yRes < 0:
        yRes = yRes * -1
    rasterDS = None

    brX = tlX + (xRes * xSize)
    brY = tlY - (yRes * ySize)

    return [tlX, brX, brY, tlY]

def get_image_bbox_in_proj(input_img, out_epsg):
    """
    A function to retrieve the bounding box in the spatial
    coordinates of the image.

    :return: (MinX, MaxX, MinY, MaxY)

    """
    import rsgislib.tools.geometrytools
    inProjWKT = get_wkt_proj_from_image(input_img)
    inSpatRef = osr.SpatialReference()
    inSpatRef.ImportFromWkt(inProjWKT)

    outSpatRef = osr.SpatialReference()
    outSpatRef.ImportFromEPSG(int(out_epsg))

    img_bbox = get_image_bbox(input_img)
    reproj_img_bbox = rsgislib.tools.geometrytools.reproj_bbox(img_bbox, inSpatRef, outSpatRef)
    return reproj_img_bbox

def get_image_band_stats(input_img, band, compute=True):
    """
    A function which calls the GDAL function on the band selected to calculate the pixel stats
    (min, max, mean, standard deviation).

    :param input_img: input image file path
    :param band: specified image band for which stats are to be calculated (starts at 1).
    :param compute: whether the stats should be calculated (True; Default) or an approximation or pre-calculated stats are OK (False).

    :return: stats (min, max, mean, stddev)

    """
    img_ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if img_ds is None:
        raise Exception("Could not open image: '{}'".format(input_img))
    n_bands = img_ds.RasterCount

    if band > 0 and band <= n_bands:
        img_band = img_ds.GetRasterBand(band)
        if img_band is None:
            raise Exception("Could not open image band ('{0}') from : '{1}'".format(band, input_img))
        img_stats = img_band.ComputeStatistics((not compute))
    else:
        raise Exception("Band specified is not within the image: '{}'".format(input_img))
    return img_stats

def get_image_band_count(input_img):
    """
    A function to retrieve the number of image bands in an image file.

    :return: nBands

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')

    nBands = rasterDS.RasterCount
    rasterDS = None
    return nBands

def get_image_no_data_value(input_img, band=1):
    """
    A function to retrieve the no data value for the image
    (from band; default 1).

    :return: number

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')

    noDataVal = rasterDS.GetRasterBand(band).GetNoDataValue()
    rasterDS = None
    return noDataVal

def set_image_no_data_value(input_img, noDataValue, band=None):
    """
    A function to set the no data value for an image.
    If band is not specified sets value for all bands.

    """
    rasterDS = gdal.Open(input_img, gdal.GA_Update)
    if rasterDS is None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')

    if band is not None:
        rasterDS.GetRasterBand(band).SetNoDataValue(noDataValue)
    else:
        for b in range(rasterDS.RasterCount):
            rasterDS.GetRasterBand(b + 1).SetNoDataValue(noDataValue)

    rasterDS = None

def get_img_band_colour_interp(input_img, band):
    """
    A function to get the colour interpretation for a specific band.

    :return: is a GDALColorInterp value:

    * GCI_Undefined=0,
    * GCI_GrayIndex=1,
    * GCI_PaletteIndex=2,
    * GCI_RedBand=3,
    * GCI_GreenBand=4,
    * GCI_BlueBand=5,
    * GCI_AlphaBand=6,
    * GCI_HueBand=7,
    * GCI_SaturationBand=8,
    * GCI_LightnessBand=9,
    * GCI_CyanBand=10,
    * GCI_MagentaBand=11,
    * GCI_YellowBand=12,
    * GCI_BlackBand=13,
    * GCI_YCbCr_YBand=14,
    * GCI_YCbCr_CbBand=15,
    * GCI_YCbCr_CrBand=16,
    * GCI_Max=16

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS is None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    clrItrpVal = rasterDS.GetRasterBand(band).GetRasterColorInterpretation()
    rasterDS = None
    return clrItrpVal

def set_img_band_colour_interp(input_img, band, clrItrpVal):
    """
    A function to set the colour interpretation for a specific band.
    input is a GDALColorInterp value:

    * GCI_Undefined=0,
    * GCI_GrayIndex=1,
    * GCI_PaletteIndex=2,
    * GCI_RedBand=3,
    * GCI_GreenBand=4,
    * GCI_BlueBand=5,
    * GCI_AlphaBand=6,
    * GCI_HueBand=7,
    * GCI_SaturationBand=8,
    * GCI_LightnessBand=9,
    * GCI_CyanBand=10,
    * GCI_MagentaBand=11,
    * GCI_YellowBand=12,
    * GCI_BlackBand=13,
    * GCI_YCbCr_YBand=14,
    * GCI_YCbCr_CbBand=15,
    * GCI_YCbCr_CrBand=16,
    * GCI_Max=16

    """
    rasterDS = gdal.Open(input_img, gdal.GA_Update)
    if rasterDS is None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    rasterDS.GetRasterBand(band).SetColorInterpretation(clrItrpVal)
    rasterDS = None

def get_wkt_proj_from_image(input_img):
    """
    A function which returns the WKT string representing the projection
    of the input image.

    :return: string

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    projStr = rasterDS.GetProjection()
    rasterDS = None
    return projStr

def get_epsg_proj_from_image(input_img):
    """
    Using GDAL to return the EPSG code for the input layer.
    :return: EPSG code
    """
    epsgCode = None
    try:
        layerDS = gdal.Open(input_img, gdal.GA_ReadOnly)
        if layerDS == None:
            raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
        projStr = layerDS.GetProjection()
        layerDS = None

        spatRef = osr.SpatialReference()
        spatRef.ImportFromWkt(projStr)
        spatRef.AutoIdentifyEPSG()
        epsgCode = spatRef.GetAuthorityCode(None)
        if epsgCode is not None:
            epsgCode = int(epsgCode)
    except Exception:
        epsgCode = None
    return epsgCode

def get_image_files(input_img):
    """
    A function which returns a list of the files associated (e.g., header etc.)
    with the input image file.

    :return: lists

    """
    imgDS = gdal.Open(input_img)
    fileList = imgDS.GetFileList()
    imgDS = None
    return fileList

def get_utm_zone(input_img):
    """
    A function which returns a string with the UTM (XXN | XXS) zone of the input image
    but only if it is projected within the UTM projection/coordinate system.

    :return: string

    """
    rasterDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if rasterDS == None:
        raise rsgislib.RSGISPyException('Could not open raster image: \'' + input_img + '\'')
    projStr = rasterDS.GetProjection()
    rasterDS = None

    spatRef = osr.SpatialReference()
    spatRef.ImportFromWkt(projStr)
    utmZone = None
    if spatRef.IsProjected():
        projName = spatRef.GetAttrValue('projcs')
        zone = spatRef.GetUTMZone()
        if zone != 0:
            if zone < 0:
                utmZone = str(zone * (-1))
                if len(utmZone) == 1:
                    utmZone = '0' + utmZone
                utmZone = utmZone + 'S'
            else:
                utmZone = str(zone)
                if len(utmZone) == 1:
                    utmZone = '0' + utmZone
                utmZone = utmZone + 'N'
    return utmZone


def do_gdal_layers_have_same_proj(in_a_img, in_b_img):
    """
    A function which tests whether two gdal compatiable layers are in the same
    projection/coordinate system. This is done using the GDAL SpatialReference
    function AutoIdentifyEPSG. If the identified EPSG codes are different then
    False is returned otherwise True.

    :return: boolean

    """
    layer1EPSG = get_epsg_proj_from_image(in_a_img)
    layer2EPSG = get_epsg_proj_from_image(in_b_img)

    sameEPSG = False
    if layer1EPSG == layer2EPSG:
        sameEPSG = True

    return sameEPSG



def set_band_names(input_img, band_names, feedback=False):
    """A utility function to set band names.
Where:

:param inImage: is the input image
:param band_names: is a list of band names
:param feedback: is a boolean specifying whether feedback will be printed to the console (True= Printed / False (default) Not Printed)

Example::

    from rsgislib import imageutils

    input_img = 'injune_p142_casi_sub_utm.kea'
    band_names = ['446nm','530nm','549nm','569nm','598nm','633nm','680nm','696nm','714nm','732nm','741nm','752nm','800nm','838nm']
    
    imageutils.set_band_names(input_img, band_names)
    
"""
    dataset = gdal.Open(input_img, gdal.GA_Update)
    
    for i in range(len(band_names)):
        band = i+1
        bandName = band_names[i]

        imgBand = dataset.GetRasterBand(band)
        # Check the image band is available
        if not imgBand is None:
            if feedback:
                print('Setting Band {0} to "{1}"'.format(band, bandName))
            imgBand.SetDescription(bandName)
        else:
            raise Exception("Could not open the image band: ", band)

def get_band_names(input_img):
    """
A utility function to get band names.

Where:

:param inImage: is the input image

:return: list of band names

Example::

    from rsgislib import imageutils

    input_img = 'injune_p142_casi_sub_utm.kea'
    bandNames = imageutils.get_band_names(input_img)

"""
    dataset = gdal.Open(input_img, gdal.GA_Update)
    bandNames = list()
    
    for i in range(dataset.RasterCount):
        imgBand = dataset.GetRasterBand(i+1)
        # Check the image band is available
        if not imgBand is None:
            bandNames.append(imgBand.GetDescription())
        else:
            raise Exception("Could not open the image band: {}".format(imgBand))
    return bandNames


def set_img_thematic(input_img):
    """
Set all image bands to be thematic. 

:param input_img: The file for which the bands are to be set as thematic

"""
    ds = gdal.Open(input_img, gdal.GA_Update)
    if ds == None:
        raise Exception("Could not open the input_img.")
    for bandnum in range(ds.RasterCount):
        band = ds.GetRasterBand(bandnum + 1)
        band.SetMetadataItem('LAYER_TYPE', 'thematic')
    ds = None


def set_img_not_thematic(input_img):
    """
Set all image bands to be not thematic (athematic).

:param input_img: The file for which the bands are to be set as not thematic (athematic)

"""
    ds = gdal.Open(input_img, gdal.GA_Update)
    if ds == None:
        raise Exception("Could not open the input_img.")
    for bandnum in range(ds.RasterCount):
        band = ds.GetRasterBand(bandnum + 1)
        band.SetMetadataItem('LAYER_TYPE', 'athematic')
    ds = None


def has_gcps(input_img):
    """
Test whether the input image has GCPs - returns boolean

:param input_img: input image file

:return: boolean True - has GCPs; False - does not have GCPs

"""
    raster = gdal.Open(input_img, gdal.GA_ReadOnly)
    if raster == None:
        raise Exception("Could not open the input_img.")
    numGCPs = raster.GetGCPCount()
    hasGCPs = False
    if numGCPs > 0:
        hasGCPs = True
    raster = None
    return hasGCPs


def copy_gcps(input_img, output_img):
    """
Copy the GCPs from the input_img to the output_img

:param input_img: Raster layer with GCPs
:param output_img: Raster layer to which GCPs will be added
    
"""
    srcDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if srcDS == None:
        raise Exception("Could not open the input_img.")
    destDS = gdal.Open(output_img, gdal.GA_Update)
    if destDS == None:
        srcDS = None
        raise Exception("Could not open the output_img.")

    numGCPs = srcDS.GetGCPCount()
    if numGCPs > 0:
        gcpProj = srcDS.GetGCPProjection()
        gcpList = srcDS.GetGCPs()
        destDS.SetGCPs(gcpList, gcpProj)

    srcDS = None
    destDS = None


def set_img_band_metadata(input_img, band, meta_field_name, meta_field_value):
    """
    Function to set image band metadata value.

    :param input_img: the input image data
    :param band: the image band for the meta-data to be written to
    :param meta_field_name: the field name of the meta-data
    :param meta_field_value: the value of the meta-data to be written.

    """
    if band < 1:
        raise Exception("The band number must be 1 or greater; note band numbering starts at 1.")

    ds = gdal.Open(input_img, gdal.GA_Update)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    n_bands = ds.RasterCount
    if band > n_bands:
        raise Exception("Band {} is not within the image file, which has {} bands".format(band, n_bands))

    band_obj = ds.GetRasterBand(band)
    band_obj.SetMetadataItem(meta_field_name, "{}".format(meta_field_value))
    ds = None


def get_img_band_metadata(input_img, band, meta_field_name):
    """
    Function to get image band metadata value.

    :param input_img: the input image data
    :param band: the image band for the meta-data to be read
    :param meta_field_name: the field name of the meta-data

    """
    if band < 1:
        raise Exception("The band number must be 1 or greater; note band numbering starts at 1.")

    ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    n_bands = ds.RasterCount
    if band > n_bands:
        raise Exception("Band {} is not within the image file, which has {} bands".format(band, n_bands))

    band_obj = ds.GetRasterBand(band)
    meta_field_value = band_obj.GetMetadataItem(meta_field_name)
    print(band_obj.GetMetadata_Dict())
    ds = None

    return meta_field_value


def get_img_band_metadata_fields(input_img, band):
    """
    Function to get a list of the image band metadata names.

    :param input_img: the input image data
    :param band: the image band for the meta-data to be read

    """
    if band < 1:
        raise Exception("The band number must be 1 or greater; note band numbering starts at 1.")

    ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    n_bands = ds.RasterCount
    if band > n_bands:
        raise Exception("Band {} is not within the image file, which has {} bands".format(band, n_bands))

    band_obj = ds.GetRasterBand(band)
    meta_data_dict = band_obj.GetMetadata_Dict()
    ds = None

    return list(meta_data_dict.keys())


def get_img_band_metadata_fields_dict(input_img, band):
    """
    Function to get image band metadata names and values as a dict.

    :param input_img: the input image data
    :param band: the image band for the meta-data to be read

    """
    if band < 1:
        raise Exception("The band number must be 1 or greater; note band numbering starts at 1.")

    ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    n_bands = ds.RasterCount
    if band > n_bands:
        raise Exception("Band {} is not within the image file, which has {} bands".format(band, n_bands))

    band_obj = ds.GetRasterBand(band)
    meta_data_dict = band_obj.GetMetadata_Dict()
    ds = None

    return meta_data_dict


def set_img_metadata(input_img, meta_field_name, meta_field_value):
    """
    Function to set image metadata value.

    :param input_img: the input image data
    :param meta_field_name: the field name of the meta-data
    :param meta_field_value: the value of the meta-data to be written.

    """
    ds = gdal.Open(input_img, gdal.GA_Update)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    ds.SetMetadataItem(meta_field_name, "{}".format(meta_field_value))
    ds = None


def get_img_metadata(input_img, meta_field_name):
    """
    Function to get image metadata value.

    :param input_img: the input image data
    :param meta_field_name: the field name of the meta-data

    """
    ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    meta_field_value = ds.GetMetadataItem(meta_field_name)
    ds = None
    return meta_field_value


def get_img_metadata_fields(input_img):
    """
    Function to get a list of the image metadata names.

    :param input_img: the input image data
    :param band: the image band for the meta-data to be read

    """
    ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    meta_data_dict = ds.GetMetadata_Dict()
    ds = None

    return list(meta_data_dict.keys())


def get_img_metadata_fields_dict(input_img):
    """
    Function to get image metadata names and values as a dict.

    :param input_img: the input image data

    """
    ds = gdal.Open(input_img, gdal.GA_ReadOnly)
    if ds == None:
        raise Exception("Could not open the image file: {}".format(input_img))

    meta_data_dict = ds.GetMetadata_Dict()
    ds = None

    return meta_data_dict


def create_blank_image_py(output_img, n_bands, width, height, tlX, tlY, out_img_res_x, out_img_res_y, wkt_string,
                          gdalformat, datatype, options=[], no_data_val=0):
    """
    Create a blank output image file - this is a pure python implementation of rsgislib.imageutils.createBlankImage

    :param output_img: the output file and path.
    :param n_bands: the number of output image bands.
    :param width: the number of x pixels.
    :param height: the number of Y pixels.
    :param tlX: the top-left corner x coordinate
    :param tlY: the top-left corner y coordinate
    :param out_img_res_x: the output image resolution in the x axis
    :param out_img_res_y: the output image resolution in the y axis
    :param wkt_string: a WKT string with the output image projection
    :param gdalformat: the output image file format.
    :param datatype: the output image data type - needs to be a rsgislib datatype (e.g., )
    :param options: image creation options e.g., ["TILED=YES", "INTERLEAVE=PIXEL", "COMPRESS=LZW", "BIGTIFF=YES"]
    :param no_data_val: the output image no data value.

    """
    gdal_data_type = rsgislib.get_gdal_datatype(datatype)
    gdal_driver = gdal.GetDriverByName(gdalformat)
    out_img_ds_obj = gdal_driver.Create(output_img, width, height, n_bands, gdal_data_type, options=options)
    out_img_ds_obj.SetGeoTransform((tlX, out_img_res_x, 0, tlY, 0, out_img_res_y))
    out_img_ds_obj.SetProjection(wkt_string)

    raster = numpy.zeros((height, width), dtype=rsgislib.get_numpy_datatype(datatype))
    raster[...] = no_data_val
    for band in range(n_bands):
        band_obj = out_img_ds_obj.GetRasterBand(band + 1)
        band_obj.SetNoDataValue(no_data_val)
        band_obj.WriteArray(raster)
    out_img_ds_obj = None


def create_blank_buf_img_from_ref_img(input_img, output_img, gdalformat, datatype, buf_pxl_ext=None, buf_spt_ext=None,
                                      no_data_val=None):
    """
    A function to create a new image file based on the input image but buffered by the specified amount
    (e.g., 100 pixels bigger on all sides. The buffer amount can ba specified in pixels or spatial units.
    If non-None value is given for both inputs then an error will be produced. By default the no data value
    will be taken from the input image header but if not available or specified within the function call
    then that value will be used.

    :param input_img: input reference image
    :param output_img: output image file.
    :param gdalformat: output image file format.
    :param datatype: is a rsgislib.TYPE_* value providing the data type of the output image.
    :param buf_pxl_ext: the amount the input image will be buffered in pixels.
    :param buf_spt_ext: the amount the input image will be buffered in spatial distance,
                    units are defined from the projection of the input image.
    :param no_data_val: Optional no data value. If None then the no data value will be
                    taken from the input image.

    """
    if (buf_pxl_ext is None) and (buf_spt_ext is None):
        raise Exception("You must specify either the buf_pxl_ext or buf_spt_ext value.")

    if (buf_pxl_ext is not None) and (buf_spt_ext is not None):
        raise Exception("You cannot specify both the buf_pxl_ext or buf_spt_ext value.")

    if no_data_val is None:
        no_data_val = get_image_no_data_value(input_img)

        if no_data_val is None:
            raise Exception("You must specify a no data value ")

    x_res, y_res = get_image_res(input_img, abs_vals=False)
    x_res_abs = abs(x_res)
    y_res_abs = abs(y_res)
    x_in_size, y_in_size = get_image_size(input_img)
    in_img_bbox = get_image_bbox(input_img)
    n_bands = get_image_band_count(input_img)
    wkt_str = get_wkt_proj_from_image(input_img)

    if buf_spt_ext is not None:
        buf_pxl_ext_x = math.ceil(buf_spt_ext / x_res_abs)
        buf_pxl_ext_y = math.ceil(buf_spt_ext / y_res_abs)

        x_out_size = x_in_size + (2 * buf_pxl_ext_x)
        y_out_size = y_in_size + (2 * buf_pxl_ext_y)

        out_tl_x = in_img_bbox[0] - (buf_pxl_ext_x * x_res_abs)
        out_tl_y = in_img_bbox[3] + (buf_pxl_ext_y * y_res_abs)
    else:
        x_out_size = x_in_size + (2 * buf_pxl_ext)
        y_out_size = y_in_size + (2 * buf_pxl_ext)

        out_tl_x = in_img_bbox[0] - (buf_pxl_ext * x_res_abs)
        out_tl_y = in_img_bbox[3] + (buf_pxl_ext * y_res_abs)

    createBlankImage(output_img, n_bands, x_out_size, y_out_size, out_tl_x, out_tl_y, x_res, y_res,
                                         no_data_val, '', wkt_str, gdalformat, datatype)


def create_blank_img_from_ref_vector(inVecFile, inVecLyr, outputImg, outImgRes, outImgNBands, gdalformat, datatype):
    """
A function to create a new image file based on a vector layer to define the extent and projection
of the output image. 

:param inVecFile: input vector file.
:param inVecLyr: name of the vector layer, if None then assume the layer name will be the same as the file
                 name of the input vector file.
:param outputImg: output image file.
:param outImgRes: output image resolution, square pixels so a single value.
:param outImgNBands: the number of image bands in the output image
:param gdalformat: output image file format.
:param datatype: is a rsgislib.TYPE_* value providing the data type of the output image

"""

    import rsgislib.vectorutils
    import rsgislib.tools.geometrytools
    baseExtent = rsgislib.vectorutils.getVecLayerExtent(inVecFile, inVecLyr)
    xMin, xMax, yMin, yMax = rsgislib.tools.geometrytools.findExtentOnGrid(baseExtent, outImgRes, full_contain=True)

    tlX = xMin
    tlY = yMax
    
    widthCoord = xMax - xMin
    heightCoord = yMax - yMin
    
    width = int(math.ceil(widthCoord/outImgRes))
    height = int(math.ceil(heightCoord/outImgRes))
    
    wktString = rsgislib.vectorutils.getProjWKTFromVec(inVecFile)

    rsgislib.imageutils.createBlankImage(outputImg, outImgNBands, width, height, tlX, tlY,
                                         outImgRes, (outImgRes*-1), 0.0, '', wktString, gdalformat, datatype)
    

def create_copy_image_vec_extent_snap_to_grid(inVecFile, inVecLyr, outputImg, outImgRes, outImgNBands, gdalformat, datatype, bufnpxl=0):
    """
A function to create a new image file based on a vector layer to define the extent and projection
of the output image. The image file extent is snapped on to the grid defined by the vector layer.

:param inVecFile: input vector file.
:param inVecLyr: name of the vector layer, if None then assume the layer name will be the same as the file
                 name of the input vector file.
:param outputImg: output image file.
:param outImgRes: output image resolution, square pixels so a single value.
:param outImgNBands: the number of image bands in the output image
:param gdalformat: output image file format.
:param datatype: is a rsgislib.TYPE_* value providing the data type of the output image
:param bufnpxl: is an integer specifying the number of pixels to buffer the vector file extent by.

"""
    import rsgislib.vectorutils
    import rsgislib.tools.geometrytools
    
    vec_bbox = rsgislib.vectorutils.getVecLayerExtent(inVecFile, layerName=inVecLyr, computeIfExp=True)
    xMin = vec_bbox[0] - (outImgRes * bufnpxl)
    xMax = vec_bbox[1] + (outImgRes * bufnpxl)
    yMin = vec_bbox[2] - (outImgRes * bufnpxl)
    yMax = vec_bbox[3] + (outImgRes * bufnpxl)
    xMin, xMax, yMin, yMax = rsgislib.tools.geometrytools.findExtentOnWholeNumGrid([xMin, xMax, yMin, yMax], outImgRes, True)
    
    tlX = xMin
    tlY = yMax
    
    widthCoord = xMax - xMin
    heightCoord = yMax - yMin
    
    width = int(math.ceil(widthCoord/outImgRes))
    height = int(math.ceil(heightCoord/outImgRes))
    
    wktString = rsgislib.vectorutils.getProjWKTFromVec(inVecFile)
    
    rsgislib.imageutils.createBlankImage(outputImg, outImgNBands, width, height, tlX, tlY, outImgRes, (outImgRes*-1), 0.0, '', wktString, gdalformat, datatype)
    

def create_blank_img_from_bbox(bbox, wktstr, outputImg, outImgRes, outImgPxlVal, outImgNBands, gdalformat, datatype, snap2grid=False):
    """
A function to create a new image file based on a bbox to define the extent. 

:param bbox: bounding box defining the extent of the output image (xMin, xMax, yMin, yMax)
:param wktstr: the WKT string defining the bbox and output image projection.
:param outputImg: output image file.
:param outImgRes: output image resolution, square pixels so a single value.
:param outImgPxlVal: output image pixel value.
:param outImgNBands: the number of image bands in the output image
:param gdalformat: output image file format.
:param datatype: is a rsgislib.TYPE_* value providing the data type of the output image.
:param snap2grid: optional variable to snap the image to a grid of whole numbers with respect to the image pixel resolution.

"""    
    if snap2grid:
        import rsgislib.tools.geometrytools
        bbox = rsgislib.tools.geometrytools.findExtentOnGrid(bbox, outImgRes, fullContain=True)

    xMin = bbox[0]
    xMax = bbox[1]
    yMin = bbox[2]
    yMax = bbox[3]

    tlX = xMin
    tlY = yMax
    
    widthCoord = xMax - xMin
    heightCoord = yMax - yMin
    
    width = int(math.ceil(widthCoord/outImgRes))
    height = int(math.ceil(heightCoord/outImgRes))
    
    rsgislib.imageutils.createBlankImage(outputImg, outImgNBands, width, height, tlX, tlY, outImgRes, (outImgRes*-1), outImgPxlVal, '', wktstr, gdalformat, datatype)

   
def create_image_for_each_vec_feat(vectorFile, vectorLyr, fileNameCol, outImgPath, outImgExt, outImgPxlVal, outImgNBands, outImgRes, gdalformat, datatype, snap2grid=False):
    """
A function to create a set of image files representing the extent of each feature in the 
inputted vector file.

:param vectorFile: the input vector file.
:param vectorLyr: the input vector layer
:param fileNameCol: the name of the column in the vector layer which will be used as the file names.
:param outImgPath: output file path (directory) where the images will be saved.
:param outImgExt: the file extension to be added on to the output file names.
:param outImgPxlVal: output image pixel value
:param outImgNBands: the number of image bands in the output image
:param outImgRes: output image resolution, square pixels so a single value
:param gdalformat: output image file format.
:param datatype: is a rsgislib.TYPE_* value providing the data type of the output image.
:param snap2grid: optional variable to snap the image to a grid of whole numbers with respect to the image pixel resolution.

"""
    
    dsVecFile = gdal.OpenEx(vectorFile, gdal.OF_VECTOR )
    if dsVecFile is None:
        raise Exception("Could not open '" + vectorFile + "'")
        
    lyrVecObj = dsVecFile.GetLayerByName( vectorLyr )
    if lyrVecObj is None:
        raise Exception("Could not find layer '" + vectorLyr + "'")
        
    lyrSpatRef = lyrVecObj.GetSpatialRef()
    if lyrSpatRef is not None:
        wktstr = lyrSpatRef.ExportToWkt()
    else:
        wktstr = ''
        
    colExists = False
    feat_idx = 0
    lyrDefn = lyrVecObj.GetLayerDefn()
    for i in range( lyrDefn.GetFieldCount() ):
        if lyrDefn.GetFieldDefn(i).GetName().lower() == fileNameCol.lower():
            feat_idx = i
            colExists = True
            break
    
    if not colExists:
        dsVecFile = None
        raise Exception("The specified column does not exist in the input layer; check case as some drivers are case sensitive.")
    
    lyrVecObj.ResetReading()
    for feat in lyrVecObj:
        geom = feat.GetGeometryRef()
        if geom is not None:
            env = geom.GetEnvelope()
            tilebasename = feat.GetFieldAsString(feat_idx)
            outputImg = os.path.join(outImgPath, "{0}{1}".format(tilebasename, outImgExt))
            print(outputImg)
            create_blank_img_from_bbox(env, wktstr, outputImg, outImgRes, outImgPxlVal, outImgNBands, gdalformat, datatype, snap2grid)


def resample_image_to_match(in_ref_img, in_process_img, output_img, gdalformat, interp_method=rsgislib.INTERP_NEAREST_NEIGHBOUR, datatype=None, no_data_val=None, multicore=False):
    """
A utility function to resample an existing image to the projection and/or pixel size of another image.

Where:

:param in_ref_img: is the input reference image to which the processing image is to resampled to.
:param in_process_img: is the image which is to be resampled.
:param output_img: is the output image file.
:param gdalformat: is the gdal format for the output image.
:param interp_method: is the interpolation method used to resample the image rsgislib.INTERP_XXXX (Default: rsgislib.INTERP_NEAREST_NEIGHBOUR)
:param datatype: is the rsgislib datatype of the output image (if none then it will be the same as the input file).
:param multicore: use multiple processing cores (Default = False)

""" 
    numBands = get_image_band_count(in_process_img)
    if no_data_val == None:
        no_data_val = get_image_no_data_value(in_process_img)
    
    if datatype == None:
        datatype = get_gdal_datatype_from_img(in_process_img)

    interpolationMethod = gdal.GRA_NearestNeighbour
    if interp_method == rsgislib.INTERP_BILINEAR:
        interpolationMethod = gdal.GRA_Bilinear 
    elif interp_method == rsgislib.INTERP_LANCZOS:
        interpolationMethod = gdal.GRA_Lanczos 
    elif interp_method == rsgislib.INTERP_CUBICSPLINE:
        interpolationMethod = gdal.GRA_CubicSpline 
    elif interp_method == rsgislib.INTERP_NEAREST_NEIGHBOUR:
        interpolationMethod = gdal.GRA_NearestNeighbour 
    elif interp_method == rsgislib.INTERP_CUBIC:
        interpolationMethod = gdal.GRA_Cubic
    elif interp_method == rsgislib.INTERP_AVERAGE:
        interpolationMethod = gdal.GRA_Average
    elif interp_method == rsgislib.INTERP_MODE:
        interpolationMethod = gdal.GRA_Mode
    else:
        raise Exception("Interpolation method was not recognised or known.")
    
    backVal = 0.0
    haveNoData = False
    if no_data_val != None:
        backVal = float(no_data_val)
        haveNoData = True
    
    create_copy_img(in_ref_img, output_img, numBands, backVal, gdalformat, datatype)

    inFile = gdal.Open(in_process_img, gdal.GA_ReadOnly)
    outFile = gdal.Open(output_img, gdal.GA_Update)

    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress

    wrpOpts = []
    if multicore:
        if haveNoData:
            wrpOpts = gdal.WarpOptions(resampleAlg=interpolationMethod, srcNodata=no_data_val, dstNodata=no_data_val, multithread=True, callback=callback)
        else:
            wrpOpts = gdal.WarpOptions(resampleAlg=interpolationMethod, multithread=True, callback=callback )
    else:
        if haveNoData:
            wrpOpts = gdal.WarpOptions(resampleAlg=interpolationMethod, srcNodata=no_data_val, dstNodata=no_data_val, multithread=False, callback=callback)
        else:
            wrpOpts = gdal.WarpOptions(resampleAlg=interpolationMethod, multithread=False, callback=callback )
    
    gdal.Warp(outFile, inFile, options=wrpOpts)
    
    inFile = None
    outFile = None


def reproject_image(input_img, output_img, out_wkt, gdalformat='KEA', interp='cubic', in_wkt=None, no_data_val=0.0, out_pxl_res='image', snap_to_grid=True, multicore=False, gdal_options=[]):
    """
This function provides a tool which uses the gdalwarp function to reproject an input image. When you want an simpler
interface use the rsgislib.imageutils.gdal_warp function. This handles more automatically.

Where:

:param input_img: the input image name and path
:param output_img: the output image name and path
:param out_wkt: a WKT file representing the output projection
:param gdalformat: the output image file format (Default is KEA)
:param interp: interpolation algorithm. Options are: near, bilinear, cubic, cubicspline, lanczos, average,
               mode. (Default is cubic)
:param in_wkt: if input image is not well defined this is the input image projection as a WKT file (Default
              is None, i.e., ignored)
:param no_data_val: float representing the not data value (Default is 0.0)
:param out_pxl_res: three inputs can be provided. 1) 'image' where the output resolution will match the input
                  (Default is image). 2) 'auto' where an output resolution maintaining the image size of the
                  input image will be used. You may consider using rsgislib.imageutils.gdal_warp instead of
                  this option. 3) provide a floating point value for the image resolution (note. pixels will
                  be sqaure)
:param snap_to_grid: is a boolean specifying whether the TL pixel should be snapped to a multiple of the pixel
                  resolution (Default is True).
:param nCores: the number of processing cores available for processing (-1 is all cores: Default=-1)
:param gdal_options: GDAL file creation options e.g., ["TILED=YES", "COMPRESS=LZW", "BIGTIFF=YES"]

    """
    import rsgislib
    import rsgislib.tools.utils
    import rsgislib.tools.geometrytools
    eResampleAlg = gdal.GRA_CubicSpline
    if interp == 'near':
        eResampleAlg = gdal.GRA_NearestNeighbour
    elif interp == 'bilinear':
        eResampleAlg = gdal.GRA_Bilinear
    elif interp == 'cubic':
        eResampleAlg = gdal.GRA_Cubic
    elif interp == 'cubicspline':
        eResampleAlg = gdal.GRA_CubicSpline
    elif interp == 'lanczos':
        eResampleAlg = gdal.GRA_Lanczos
    elif interp == 'average':
        eResampleAlg = gdal.GRA_Average
    elif interp == 'mode':
        eResampleAlg = gdal.GRA_Mode
    else:
        raise Exception('The interpolation algorithm was not recogonised: \'' + interp + '\'')
    
    if not os.path.exists(input_img):
        raise Exception('The input image file does not exist: \'' + input_img + '\'')
    
    inImgDS = gdal.Open(input_img, gdal.GA_ReadOnly)
    if inImgDS is None:
        raise Exception('Could not open the Input Image: \'' + input_img + '\'')
    
    inImgProj = osr.SpatialReference()
    if not in_wkt is None:
        if not os.path.exists(in_wkt):
            raise Exception('The input WKT file does not exist: \'' + in_wkt + '\'')
        inWKTStr = rsgislib.tools.utils.read_text_file_no_new_lines(in_wkt)
        inImgProj.ImportFromWkt(inWKTStr)
    else:
        inImgProj.ImportFromWkt(inImgDS.GetProjectionRef())
        
    if not os.path.exists(out_wkt):
        raise Exception('The output WKT file does not exist: \'' + out_wkt + '\'')
    outImgProj = osr.SpatialReference()
    outWKTStr = rsgislib.tools.utils.read_text_file_no_new_lines(out_wkt)
    outImgProj.ImportFromWkt(outWKTStr)
    
    geoTransform = inImgDS.GetGeoTransform()
    if geoTransform is None:
        raise Exception('Could read the geotransform from the Input Image: \'' + input_img + '\'')
    
    xPxlRes = geoTransform[1]
    yPxlRes = geoTransform[5]
    
    inRes = xPxlRes
    if math.fabs(yPxlRes) < math.fabs(xPxlRes):
        inRes = math.fabs(yPxlRes)
    
    xSize = inImgDS.RasterXSize
    ySize = inImgDS.RasterYSize
    
    tlXIn = geoTransform[0]
    tlYIn = geoTransform[3]
    
    brXIn = tlXIn + (xSize * math.fabs(xPxlRes))
    brYIn = tlYIn - (ySize * math.fabs(yPxlRes))
    
    trXIn = brXIn
    trYIn = tlYIn
    
    blXIn = tlXIn
    blYIn = trYIn
    
    numBands = inImgDS.RasterCount
    
    inImgBand = inImgDS.GetRasterBand( 1 )
    gdalDataType = gdal.GetDataTypeName(inImgBand.DataType)
    rsgisDataType = rsgislib.get_rsgislib_datatype(gdalDataType)

    tlXOut, tlYOut = rsgislib.tools.geometrytools.reprojPoint(inImgProj, outImgProj, tlXIn, tlYIn)
    brXOut, brYOut = rsgislib.tools.geometrytools.reprojPoint(inImgProj, outImgProj, brXIn, brYIn)
    trXOut, trYOut = rsgislib.tools.geometrytools.reprojPoint(inImgProj, outImgProj, trXIn, trYIn)
    blXOut, blYOut = rsgislib.tools.geometrytools.reprojPoint(inImgProj, outImgProj, blXIn, blYIn)

    xValsOut = [tlXOut, brXOut, trXOut, blXOut]
    yValsOut = [tlYOut, brYOut, trYOut, blYOut]
    
    xMax = max(xValsOut)
    xMin = min(xValsOut)
    
    yMax = max(yValsOut)
    yMin = min(yValsOut)
    
    out_pxl_res = str(out_pxl_res).strip()
    outRes = 0.0
    if rsgislib.tools.utils.isNumber(out_pxl_res):
        outRes = math.fabs(float(out_pxl_res))
    elif out_pxl_res == 'image':
        outRes = inRes
    elif out_pxl_res == 'auto':
        xOutRes = (brXOut - tlXOut) / xSize
        yOutRes = (tlYOut - brYOut) / ySize
        outRes = xOutRes
        if yOutRes < xOutRes:
            outRes = yOutRes
    else: 
        raise Exception('Was not able to defined the output resolution. Check Input: \'' + out_pxl_res + '\'')

    outTLX = xMin
    outTLY = yMax
    outWidth = int(round((xMax - xMin) / outRes)) + 1
    outHeight = int(round((yMax - yMin) / outRes)) + 1
    
    if snap_to_grid:
    
        xLeft = outTLX % outRes
        yLeft = outTLY % outRes
        
        outTLX = (outTLX-xLeft) - (5 * outRes)
        outTLY = ((outTLY-yLeft) + outRes) + (5 * outRes)
        
        outWidth = int(round((xMax - xMin) / outRes)) + 10
        outHeight = int(round((yMax - yMin) / outRes)) + 10
    
    print('Creating blank image')
    rsgislib.imageutils.create_blank_image_py(output_img, numBands, outWidth, outHeight, outTLX, outTLY, outRes,
                                              (outRes * (-1)), outWKTStr, gdalformat, rsgisDataType, options=gdal_options, no_data_val=no_data_val)

    outImgDS = gdal.Open(output_img, gdal.GA_Update)
    
    for i in range(numBands):
        outImgDS.GetRasterBand(i+1).SetNoDataValue(no_data_val)

    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress

    print("Performing the reprojection")
    wrpOpts = []
    if multicore:
        wrpOpts = gdal.WarpOptions(resampleAlg=eResampleAlg, srcNodata=no_data_val, dstNodata=no_data_val, multithread=True, callback=callback)
    else:
        wrpOpts = gdal.WarpOptions(resampleAlg=eResampleAlg, srcNodata=no_data_val, dstNodata=no_data_val, multithread=False, callback=callback)

    gdal.Warp(outImgDS, inImgDS, options=wrpOpts)

    inImgDS = None
    outImgDS = None


def gdal_warp(input_img, output_img, out_epsg, interp='near', gdalformat='KEA', use_multi_threaded=True, options=[]):
    """
    A function which runs GDAL Warp function to tranform an image from one projection to another. Use this function
    when you want GDAL to do procesing of pixel size and image size automatically. rsgislib.imageutils.reproject_image
    should be used when you want to put the output image on a particular grid etc.

    :param input_img: input image file
    :param output_img: output image file
    :param out_epsg: the EPSG for the output image file.
    :param interp: interpolation algorithm. Options are: near, bilinear, cubic, cubicspline, lanczos, average, mode. (Default is near)
    :param gdalformat: output image file format
    :param use_multi_threaded: Use multiple cores for processing (Default: True).
    :param options: GDAL file creation options e.g., ["TILED=YES", "COMPRESS=LZW", "BIGTIFF=YES"]

    """
    from osgeo import gdal
    gdal.UseExceptions()
    in_no_data_val = get_image_no_data_value(input_img)
    in_epsg = get_epsg_proj_from_image(input_img)
    img_data_type = get_gdal_datatype_name_from_img(input_img)

    eResampleAlg = gdal.GRA_CubicSpline
    if interp == 'near':
        eResampleAlg = gdal.GRA_NearestNeighbour
    elif interp == 'bilinear':
        eResampleAlg = gdal.GRA_Bilinear
    elif interp == 'cubic':
        eResampleAlg = gdal.GRA_Cubic
    elif interp == 'cubicspline':
        eResampleAlg = gdal.GRA_CubicSpline
    elif interp == 'lanczos':
        eResampleAlg = gdal.GRA_Lanczos
    elif interp == 'average':
        eResampleAlg = gdal.GRA_Average
    elif interp == 'mode':
        eResampleAlg = gdal.GRA_Mode
    else:
        raise Exception('The interpolation algorithm was not recogonised: \'' + interp + '\'')

    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress
    warp_opts = gdal.WarpOptions(format=gdalformat, srcSRS="EPSG:{}".format(in_epsg), dstSRS="EPSG:{}".format(out_epsg),
                                 resampleAlg=eResampleAlg, srcNodata=in_no_data_val, dstNodata=in_no_data_val,
                                 callback=callback, creationOptions=options, outputType=img_data_type,
                                 workingType=gdal.GDT_Float32, multithread=use_multi_threaded)
    gdal.Warp(output_img, input_img, options=warp_opts)

def subset_pxl_bbox(input_img, outputimage, gdalformat, datatype, xMinPxl, xMaxPxl, yMinPxl, yMaxPxl):
    """
Function to subset an input image using a defined pixel bbox.

:param input_img: input image to be subset.
:param outputimage: output image file.
:param gdalformat: output image file format
:param datatype: datatype is a rsgislib.TYPE_* value providing the data type of the output image.
:param xMinPxl: min x in pixels
:param xMaxPxl: max x in pixels
:param yMinPxl: min y in pixels
:param yMaxPxl: max y in pixels

"""
    bbox = get_image_bbox(input_img)
    xRes, yRes = get_image_res(input_img, abs_vals=True)
    xSize, ySize = get_image_size(input_img)
    
    if (xMaxPxl > xSize) or (yMaxPxl > ySize):
        raise Exception("The pixel extent defined is bigger than the input image.")
    
    xMin = bbox[0] + (xMinPxl * xRes)
    xMax = bbox[0] + (xMaxPxl * xRes)
    yMin = bbox[2] + (yMinPxl * yRes)
    yMax = bbox[2] + (yMaxPxl * yRes)
    
    rsgislib.imageutils.subsetbbox(input_img, outputimage, gdalformat, datatype, xMin, xMax, yMin, yMax)

def create_tiles_multi_core(input_img, baseimage, width, height, gdalformat, datatype, ext, ncores=1):
    """
Function to generate a set of tiles for the input image.

:param input_img: input image to be subset.
:param baseimage: output image files base path.
:param width: width in pixels of the tiles.
:param height: height in pixels of the tiles.
:param gdalformat: output image file format
:param datatype: datatype is a rsgislib.TYPE_* value providing the data type of the output image.
:param ext: output file extension to be added to the baseimage path (e.g., kea)
:param ncores: number of cores to be used; uses python multiprocessing module.

"""
    import multiprocessing
    xSize, ySize = get_image_size(input_img)
    
    n_full_xtiles = math.floor(xSize/width)
    x_remain_width = xSize - (n_full_xtiles * width)
    n_full_ytiles = math.floor(ySize/height)
    y_remain_height = ySize - (n_full_ytiles * height)
    
    tiles = []
    
    for ytile in range(n_full_ytiles):
        y_pxl_min = ytile * height
        y_pxl_max = y_pxl_min + height
    
        for xtile in range(n_full_xtiles):
            x_pxl_min = xtile * width
            x_pxl_max = x_pxl_min + width
            tiles.append({'tile':'x{0}y{1}'.format(xtile+1, ytile+1), 'bbox':[x_pxl_min, x_pxl_max, y_pxl_min, y_pxl_max]})

        if x_remain_width > 0:
            x_pxl_min = n_full_xtiles * width
            x_pxl_max = x_pxl_min + x_remain_width
            tiles.append({'tile':'x{0}y{1}'.format(n_full_xtiles+1, ytile+1), 'bbox':[x_pxl_min, x_pxl_max, y_pxl_min, y_pxl_max]})
    
    if y_remain_height > 0:
        y_pxl_min = n_full_ytiles * height
        y_pxl_max = y_pxl_min + y_remain_height
        
        for xtile in range(n_full_xtiles):
            x_pxl_min = xtile * width
            x_pxl_max = x_pxl_min + width
            tiles.append({'tile':'x{0}y{1}'.format(xtile+1, n_full_ytiles+1), 'bbox':[x_pxl_min, x_pxl_max, y_pxl_min, y_pxl_max]})

        if x_remain_width > 0:
            x_pxl_min = n_full_xtiles * width
            x_pxl_max = x_pxl_min + x_remain_width
            tiles.append({'tile':'x{0}y{1}'.format(n_full_xtiles+1, n_full_ytiles+1), 'bbox':[x_pxl_min, x_pxl_max, y_pxl_min, y_pxl_max]})
    
    for tile in tiles:
        tile['input_img'] = input_img
        tile['outfile'] = "{0}_{1}.{2}".format(baseimage, tile['tile'], ext)
        tile['gdalformat'] = gdalformat
        tile['datatype'] = datatype

    def _runSubset(tileinfo):
        """ Internal function for create_tiles_multi_core for multiprocessing Pool. """
        subset_pxl_bbox(tileinfo['input_img'], tileinfo['outfile'], tileinfo['gdalformat'], tileinfo['datatype'],
                        tileinfo['bbox'][0], tileinfo['bbox'][1], tileinfo['bbox'][2], tileinfo['bbox'][3])

    poolobj = multiprocessing.Pool(ncores)
    poolobj.map(_runSubset, tiles)


def subset_imgs_to_common_extent(inImagesDict, outShpEnv, gdalformat):
    """
A command to subset a set of images to the same overlapped extent.

Where:

:param inImagesDict: is a list of dictionaries containing values for IN (input image) OUT (output image) and TYPE (data type for output)
:param outShpEnv: is a file path for the output shapefile representing the overlap extent.
:param gdalformat: is the gdal format of the output images.

Example::
    
    from rsgislib import imageutils
    
    inImagesDict = []
    inImagesDict.append({'IN': './Images/Lifeformclip.tif', 'OUT':'./Subsets/Lifeformclip_sub.kea', 'TYPE':rsgislib.TYPE_32INT})
    inImagesDict.append({'IN': './Images/chmclip.tif', 'OUT':'./Subsets/chmclip_sub.kea', 'TYPE':rsgislib.TYPE_32FLOAT})
    inImagesDict.append({'IN': './Images/peakBGclip.tif', 'OUT':'./Subsets/peakBGclip_sub.kea', 'TYPE':rsgislib.TYPE_32FLOAT})
    
    outputVector = 'imgSubExtent.shp'
    imageutils.subset_imgs_to_common_extent(inImagesDict, outputVector, 'KEA')
    
"""
    import rsgislib.vectorutils
    
    inImages = []
    for inImgDict in inImagesDict:
        inImages.append(inImgDict['IN'])
    
    rsgislib.vectorutils.findCommonImgExtent(inImages, outShpEnv, True)
    
    for inImgDict in inImagesDict:
        rsgislib.imageutils.subset(inImgDict['IN'], outShpEnv, inImgDict['OUT'], gdalformat, inImgDict['TYPE'])


def build_img_sub_dict(globFindImgsStr, outDir, suffix, ext):
    """
Automate building the dictionary of image to be used within the 
subset_imgs_to_common_extent(inImagesDict, outShpEnv, imgFormat) function.

Where:

:param globFindImgsStr: is a string to be passed to the glob module to find the input image files.
:param outDir: is the output directory path for the images.
:param suffix: is a suffix to be appended on to the end of the file name (can be a blank string, i.e., '')
:param ext: is a string with the output file extension

Example::
    
    from rsgislib import imageutils
    
    inImagesDict = imageutils.build_img_sub_dict("./Images/*.tif", "./Subsets/", "_sub", ".kea")
    print(inImagesDict)
    
    outputVector = 'imgSubExtent.shp'
    imageutils.subset_imgs_to_common_extent(inImagesDict, outputVector, 'KEA')

"""
    import glob
    import os.path
        
    inImagesDict = []
    
    inputImages = glob.glob(globFindImgsStr)
    if len(inputImages) == 0:
        raise Exception("No images were found using \'" + globFindImgsStr + "\'")
    
    for image in inputImages:
        dataset = gdal.Open(image, gdal.GA_ReadOnly)
        gdalDType = dataset.GetRasterBand(1).DataType
        dataset = None
        datatype = rsgislib.TYPE_32FLOAT
        if gdalDType == gdal.GDT_Byte:
            datatype = rsgislib.TYPE_8UINT
        elif gdalDType == gdal.GDT_Int16:
            datatype = rsgislib.TYPE_16INT
        elif gdalDType == gdal.GDT_Int32:
            datatype = rsgislib.TYPE_32INT
        elif gdalDType == gdal.GDT_UInt16:
            datatype = rsgislib.TYPE_16UINT
        elif gdalDType == gdal.GDT_UInt32:
            datatype = rsgislib.TYPE_32UINT         
        elif gdalDType == gdal.GDT_Float32:
            datatype = rsgislib.TYPE_32FLOAT
        elif gdalDType == gdal.GDT_Float64:
            datatype = rsgislib.TYPE_64FLOAT
        else:
            raise Exception("Data type of the input file was not recognised or known.")
            
        imgBase = os.path.splitext(os.path.basename(image))[0]
        outImg = os.path.join(outDir, (imgBase+suffix+ext))
        inImagesDict.append({'IN':image, 'OUT':outImg, 'TYPE':datatype})

    return inImagesDict


def calc_pixel_locations(inputImg, outputImg, gdalformat):
    """
Function which produces a 2 band output image with the X and Y locations of the image pixels.

Where:

:param inputImg: the input reference image
:param outputImg: the output image file name and path (will be same dimensions as the input)
:param gdalformat: the GDAL image file format of the output image file.

"""
    try:
        import tqdm
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress
        progress_bar = cuiprogress.GDALProgressBar()

    infiles = applier.FilenameAssociations()
    infiles.image1 = inputImg
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = outputImg
    otherargs = applier.OtherInputs()
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = True
    aControls.calcStats = False
    
    def _getXYPxlLocs(info, inputs, outputs, otherargs):
        """
        This is an internal rios function 
        """
        xBlock, yBlock = info.getBlockCoordArrays()
        outputs.outimage = numpy.stack((xBlock,yBlock))

    applier.apply(_getXYPxlLocs, infiles, outfiles, otherargs, controls=aControls)


def calc_wgs84_pixel_area(input_img, out_img, scale=10000, gdalformat="KEA"):
    """
    A function which calculates the area (in metres) of the pixel projected in WGS84.

    :param input_img: input image, for which the per-pixel area will be calculated.
    :param out_img: output image file.
    :param scale: scale the output area to unit of interest. Scale=10000(Ha),
                        Scale=1(sq m), Scale=1000000(sq km), Scale=4046.856(Acre),
                        Scale=2590000(sq miles), Scale=0.0929022668(sq feet)

    """
    import rsgislib.tools
    from rios import applier

    try:
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress

        progress_bar = cuiprogress.GDALProgressBar()

    x_res, y_res = get_image_res(input_img)

    infiles = applier.FilenameAssociations()
    infiles.input_img = input_img
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = out_img
    otherargs = applier.OtherInputs()
    otherargs.x_res = x_res
    otherargs.y_res = y_res
    otherargs.scale = float(scale)
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = False
    aControls.calcStats = False

    def _calcPixelArea(info, inputs, outputs, otherargs):
        xBlock, yBlock = info.getBlockCoordArrays()

        x_res_arr = numpy.zeros_like(yBlock, dtype=float)
        x_res_arr[...] = otherargs.x_res
        y_res_arr = numpy.zeros_like(yBlock, dtype=float)
        y_res_arr[...] = otherargs.y_res
        x_res_arr_m, y_res_arr_m = rsgislib.tools.degrees_to_metres(
            yBlock, x_res_arr, y_res_arr
        )
        outputs.outimage = numpy.expand_dims(
            (x_res_arr_m * y_res_arr_m) / otherargs.scale, axis=0
        )

    applier.apply(_calcPixelArea, infiles, outfiles, otherargs, controls=aControls)


def do_images_overlap(image1, image2, overThres=0.0):
    """
Function to test whether two images overlap with one another.
If the images have a difference projection/coordinate system then corners 

:param image1: path to first image
:param image2: path to second image
:param overThres: the amount of overlap required to return true (e.g., at least 1 pixel)

:return: Boolean specifying whether they overlap or not.

Example::

    import rsgislib.imageutils
    img = "/Users/pete/Temp/LandsatStatsImgs/MSS/ClearSkyMsks/LS1MSS_19720823_lat52lon114_r24p218_osgb_clearsky.tif"
    tile = "/Users/pete/Temp/LandsatStatsImgs/MSS/RefImages/LandsatWalesRegion_60m_tile8.kea"
    
    overlap = rsgislib.imageutils.do_images_overlap(tile, img)
    print("Images Overlap: " + str(overlap))

"""
    import rsgislib.tools.geometrytools
    overlap = True
    
    projSame = False
    if do_gdal_layers_have_same_proj(image1, image2):
        projSame = True
    
    img1DS = gdal.Open(image1, gdal.GA_ReadOnly)
    if img1DS is None:
        raise rsgislib.RSGISPyException('Could not open image: ' + image1)
        
    img2DS = gdal.Open(image2, gdal.GA_ReadOnly)
    if img2DS is None:
        raise rsgislib.RSGISPyException('Could not open image: ' + image2)

    img1GeoTransform = img1DS.GetGeoTransform()
    if img1GeoTransform is None:
        img1DS = None
        img2DS = None
        raise rsgislib.RSGISPyException('Could not get geotransform: ' + image1)
        
    img2GeoTransform = img2DS.GetGeoTransform()
    if img2GeoTransform is None:
        img1DS = None
        img2DS = None
        raise rsgislib.RSGISPyException('Could not get geotransform: ' + image2)
    
    img1TLX = img1GeoTransform[0]
    img1TLY = img1GeoTransform[3]
    
    img1BRX = img1GeoTransform[0] + (img1DS.RasterXSize * img1GeoTransform[1])
    img1BRY = img1GeoTransform[3] + (img1DS.RasterYSize * img1GeoTransform[5])
    
    img2TLX_orig = img2GeoTransform[0]
    img2TLY_orig = img2GeoTransform[3]
    
    img2BRX_orig = img2GeoTransform[0] + (img2DS.RasterXSize * img2GeoTransform[1])
    img2BRY_orig = img2GeoTransform[3] + (img2DS.RasterYSize * img2GeoTransform[5])
    
    img1EPSG = get_epsg_proj_from_image(image1)
    img2EPSG = get_epsg_proj_from_image(image2)
    
    if projSame:
        img2TLX = img2GeoTransform[0]
        img2TLY = img2GeoTransform[3]
        
        img2BRX = img2GeoTransform[0] + (img2DS.RasterXSize * img2GeoTransform[1])
        img2BRY = img2GeoTransform[3] + (img2DS.RasterYSize * img2GeoTransform[5])
    else:
        inProj = osr.SpatialReference()
        
        if img2EPSG is None:
            wktImg2 = get_wkt_proj_from_image(image2)
            if (wktImg2 is None) or (wktImg2 == ""):
                raise rsgislib.RSGISPyException('Could not retrieve EPSG or WKT for image: ' + image2)
            inProj.ImportFromWkt(wktImg2)
        else:
            inProj.ImportFromEPSG(int(img2EPSG))
        
        outProj = osr.SpatialReference()
        if img1EPSG is None:
            wktImg1 = get_wkt_proj_from_image(image1)
            if (wktImg1 is None) or (wktImg1 == ""):
                raise rsgislib.RSGISPyException('Could not retrieve EPSG or WKT for image: ' + image1)
            outProj.ImportFromWkt(wktImg1)
        else:
            outProj.ImportFromEPSG(int(img1EPSG))
        
        if img1EPSG is None:
            img1EPSG = 0

        img2TLX, img2TLY = rsgislib.tools.geometrytools.reprojPoint(inProj, outProj, img2TLX_orig, img2TLY_orig)
        img2BRX, img2BRY = rsgislib.tools.geometrytools.reprojPoint(inProj, outProj, img2BRX_orig, img2BRY_orig)
    
    xMin = img1TLX
    xMax = img1BRX
    yMin = img1BRY
    yMax = img1TLY
    
    if img2TLX > xMin:
        xMin = img2TLX
    if img2BRX < xMax:
        xMax = img2BRX
    if img2BRY > yMin:
        yMin = img2BRY
    if img2TLY < yMax:
        yMax = img2TLY
        
    if xMax - xMin <= overThres:
        overlap = False
    elif yMax - yMin <= overThres:
        overlap = False

    return overlap


def generate_random_pxl_vals_img(inputImg, outputImg, gdalformat, lowVal, upVal):
    """
Function which produces a 1 band image with random values between lowVal and upVal.

Where:

:param inputImg: the input reference image
:param outputImg: the output image file name and path (will be same dimensions as the input)
:param gdalformat: the GDAL image file format of the output image file.
:param lowVal: lower value
:param upVal: upper value

"""
    try:
        import tqdm
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress
        progress_bar = cuiprogress.GDALProgressBar()

    infiles = applier.FilenameAssociations()
    infiles.inImg = inputImg
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = outputImg
    otherargs = applier.OtherInputs()
    otherargs.lowVal = lowVal
    otherargs.upVal = upVal
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = True
    aControls.calcStats = False
    
    def _popPxlsRanVals(info, inputs, outputs, otherargs):
        """
        This is an internal rios function for generate_random_pxl_vals_img()
        """
        outputs.outimage = numpy.random.random_integers(otherargs.lowVal, high=otherargs.upVal, size=inputs.inImg.shape)
        outputs.outimage = outputs.outimage.astype(numpy.int32, copy=False)
    
    applier.apply(_popPxlsRanVals, infiles, outfiles, otherargs, controls=aControls)


def extract_img_pxl_sample(inputImg, pxlNSample, noData=None):
    """
A function which extracts a sample of pixels from the 
input image file to a number array.

:param inputImg: the image from which the random sample will be taken.
:param pxlNSample: the sample to be taken (e.g., a value of 100 will sample every 100th,
                   valid (if noData specified), pixel)
:param noData: provide a no data value which is to be ignored during processing. If None then ignored (Default: None)

:return: outputs a numpy array (n sampled values, n bands)

""" 
    # Import the RIOS image reader
    from rios.imagereader import ImageReader
    import tqdm

    first = True
    reader = ImageReader(inputImg, windowxsize=200, windowysize=200)
    for (info, block) in tqdm.tqdm(reader):
        blkShape = block.shape
        blkBands = block.reshape((blkShape[0], (blkShape[1]*blkShape[2])))
        
        blkBandsTrans = numpy.transpose(blkBands)
        
        if noData is not None:
            blkBandsTrans = blkBandsTrans[(blkBandsTrans!=noData).all(axis=1)]
        
        if blkBandsTrans.shape[0] > 0:
            nSamp = int((blkBandsTrans.shape[0])/pxlNSample)
            nSampRange = numpy.arange(0, nSamp, 1)*pxlNSample
            blkBandsTransSamp = blkBandsTrans[nSampRange]
            
            if first:
                outArr = blkBandsTransSamp
                first = False
            else:
                outArr = numpy.concatenate((outArr, blkBandsTransSamp), axis=0)
    return outArr


def extract_img_pxl_vals_in_msk(img, img_bands, img_mask, img_mask_val, no_data=None):
    """
A function which extracts the image values within a mask for the specified image bands.

:param img: the image from which the random sample will be taken.
:param img_bands: the image bands the values are to be read from.
:param img_mask: the image mask specifying the regions of interest.
:param img_mask_val: the pixel value within the mask defining the region of interest.

:return: outputs a numpy array (n values, n bands)

"""
    # Import the RIOS image reader
    from rios.imagereader import ImageReader
    import tqdm

    outArr = None
    first = True
    reader = ImageReader([img, img_mask], windowxsize=200, windowysize=200)
    for (info, block) in tqdm.tqdm(reader):
        blk_img = block[0]
        blk_msk = block[1].flatten()
        blk_img_shape = blk_img.shape

        blk_bands = blk_img.reshape((blk_img_shape[0], (blk_img_shape[1] * blk_img_shape[2])))
        band_lst = []
        for band in img_bands:
            if (band > 0) and (band <= blk_bands.shape[0]):
                band_lst.append(blk_bands[band - 1])
            else:
                raise Exception("Band ({}) specified is not within the image".format(band))
        blk_bands_sel = numpy.stack(band_lst, axis=0)
        blk_bands_trans = numpy.transpose(blk_bands_sel)

        if no_data is not None:
            blk_msk = blk_msk[(blk_bands_trans != no_data).all(axis=1)]
            blk_bands_trans = blk_bands_trans[(blk_bands_trans != no_data).all(axis=1)]

        if blk_bands_trans.shape[0] > 0:
            blk_bands_trans = blk_bands_trans[blk_msk == img_mask_val]
            if first:
                out_arr = blk_bands_trans
                first = False
            else:
                out_arr = numpy.concatenate((out_arr, blk_bands_trans), axis=0)
    return out_arr


def combine_binary_masks(msk_imgs_dict, out_img, output_lut, gdalformat='KEA'):
    """
A function which combines up to 8 binary image masks to create a single 
output image with a unique value for each combination of intersecting 
masks. A JSON LUT is also generated to identify the image values to a
'class'.

:param msk_imgs_dict: dict of input images.
:param out_img: output image file.
:param output_lut: output file path to JSON LUT file identifying the image values.
:param gdalformat: output GDAL format (e.g., KEA)

""" 
    import json
    import rsgislib.tools.utils
    import rsgislib.imagecalc
    try:
        import tqdm
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress
        progress_bar = cuiprogress.GDALProgressBar()

    in_vals_dict = dict()
    msk_imgs = list()
    for key in msk_imgs_dict.keys():
        msk_imgs.append(msk_imgs_dict[key])
        in_vals_dict[key] = [0,1]
    
    # Generated the combined mask.
    infiles = applier.FilenameAssociations()
    infiles.msk_imgs = msk_imgs
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = out_img
    otherargs = applier.OtherInputs()
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = False
    aControls.calcStats = False
    
    def _combineMsks(info, inputs, outputs, otherargs):
        out_arr = numpy.zeros_like(inputs.msk_imgs[0], dtype=numpy.uint8)        
        out_bit_arr = numpy.unpackbits(out_arr, axis=2)
        img_n = 0
        for img in inputs.msk_imgs:
            for x in range(img.shape[1]):
                for y in range(img.shape[2]):
                    if img[0,x,y] == 1:
                        out_bit_arr[0,x,(8*y)+img_n] = 1
            img_n = img_n + 1
        
        out_arr = numpy.packbits(out_bit_arr, axis=2)
        
        outputs.outimage = out_arr
    applier.apply(_combineMsks, infiles, outfiles, otherargs, controls=aControls)
    
    # find the unique output image files.
    uniq_vals = rsgislib.imagecalc.getUniqueValues(out_img, img_band=1)
    
    # find the powerset of the inputs
    possible_outputs = rsgislib.tools.utils.createVarList(in_vals_dict, val_dict=None)
    
    out_poss_lut = dict()
    for poss in possible_outputs:
        val = numpy.zeros(1, dtype=numpy.uint8)
        val_bit_arr = numpy.unpackbits(val, axis=0)
        i = 0
        for key in msk_imgs_dict.keys():
            val_bit_arr[i] = poss[key]
            i = i + 1
        out_arr = numpy.packbits(val_bit_arr)
        if out_arr[0] in uniq_vals:
            out_poss_lut[str(out_arr[0])] = poss
        
    with open(output_lut, 'w') as outJSONfile:
        json.dump(out_poss_lut, outJSONfile, sort_keys=True,indent=4, separators=(',', ': '), ensure_ascii=False)


def gdal_translate(input_img, output_img, gdalformat='KEA', options=''):
    """
    Using GDAL translate to convert input image to a different format, if GTIFF selected
    and no options are provided then a cloud optimised GeoTIFF will be outputted.

    :param input_img: Input image which is GDAL readable.
    :param output_img: The output image file.
    :param gdalformat: The output image file format
    :param options: options for the output driver (e.g., "-co TILED=YES -co COMPRESS=LZW -co BIGTIFF=YES")
    """
    if (gdalformat == 'GTIFF') and (options == ''):
        options = "-co TILED=YES -co INTERLEAVE=PIXEL -co BLOCKXSIZE=256 -co BLOCKYSIZE=256 -co COMPRESS=LZW -co BIGTIFF=YES -co COPY_SRC_OVERVIEWS=YES"

    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress

    trans_opt = gdal.TranslateOptions(format=gdalformat, options=options, callback=callback)
    gdal.Translate(output_img, input_img, options=trans_opt)


def create_stack_images_vrt(input_imgs, output_vrt_file):
    """
    A function which creates a GDAL VRT file from a set of input images by stacking the input images
    in a multi-band output file.

    :param input_imgs: A list of input images
    :param output_vrt_file: The output file location for the VRT.
    """
    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress

    build_vrt_opt = gdal.BuildVRTOptions(separate=True, callback=callback)
    gdal.BuildVRT(output_vrt_file, input_imgs, options=build_vrt_opt)


def create_mosaic_images_vrt(input_imgs, output_vrt_file, vrt_extent=None):
    """
    A function which creates a GDAL VRT file from a set of input images by mosaicking
    the input images.

    :param input_imgs: A list of input images
    :param output_vrt_file: The output file location for the VRT.
    :param vrt_extent: An optional (If None then ignored) extent (minX, minY, maxX, maxY)
                       for the VRT image.
    """
    try:
        import tqdm
        pbar = tqdm.tqdm(total=100)
        callback = lambda *args, **kw: pbar.update()
    except:
        callback = gdal.TermProgress
    if vrt_extent is not None:
        build_vrt_opt = gdal.BuildVRTOptions(outputBounds=vrt_extent, callback=callback)
    else:
        build_vrt_opt = gdal.BuildVRTOptions(callback=callback)
    gdal.BuildVRT(output_vrt_file, input_imgs, options=build_vrt_opt)


def create_vrt_band_subset(input_img, bands, out_vrt_img):
    """
    A function which creates a GDAL VRT for the input image with the bands selected in
    the input list.

    :param input_img: the input GDAL image
    :param bands: a list of bands (in the order they will be in the VRT). Note, band
                  numbering starts at 1.
    :param out_vrt_img: the output VRT file.

    """
    input_img = os.path.abspath(input_img)
    vrt_options = gdal.BuildVRTOptions(bandList=bands)
    my_vrt = gdal.BuildVRT(out_vrt_img, [input_img], options=vrt_options)
    my_vrt = None


def subset_to_vec(in_img, out_img, gdalformat, roi_vec_file, roi_vec_lyr, datatype=None, vec_epsg=None):
    """
    A function which subsets an input image using the extent of a vector layer where the
    input vector can be a different projection to the input image. Reprojection will be handled.

    :param in_img: Input Image file.
    :param out_img: Output Image file.
    :param gdalformat: Output image file format.
    :param roi_vec_file: The input vector file.
    :param roi_vec_lyr: The name of the input layer.
    :param datatype: Output image data type. If None then the datatype of the input image will be used.
    :param vec_epsg: If projection is poorly defined by the vector layer then it can be specified.
    """
    import rsgislib.vectorutils
    import rsgislib.tools.geometrytools
    if vec_epsg is None:
        vec_epsg = rsgislib.vectorutils.getProjEPSGFromVec(roi_vec_file, roi_vec_lyr)
    img_epsg = get_epsg_proj_from_image(in_img)
    if img_epsg == vec_epsg:

        projs_match = True
    else:
        img_bbox = get_image_bbox_in_proj(in_img, vec_epsg)
        projs_match = False
    img_bbox = get_image_bbox(in_img)
    vec_bbox = rsgislib.vectorutils.getVecLayerExtent(roi_vec_file, roi_vec_lyr, computeIfExp=True)
    if img_epsg != vec_epsg:
        vec_bbox = rsgislib.tools.geometrytools.reprojBBOX_epsg(vec_bbox, vec_epsg, img_epsg)

    if rsgislib.tools.geometrytools.do_bboxes_intersect(img_bbox, vec_bbox):
        common_bbox = rsgislib.tools.geometrytools.bbox_intersection(img_bbox, vec_bbox)
        if datatype == None:
            datatype = get_gdal_datatype_from_img(in_img)
        rsgislib.imageutils.subsetbbox(in_img, out_img, gdalformat, datatype, common_bbox[0], common_bbox[1],
                                       common_bbox[2], common_bbox[3])
    else:
        raise Exception("The image and vector do not intersect and therefore the image cannot be subset.")


def mask_img_with_vec(input_img, output_img, gdalformat, roi_vec_file, roi_vec_lyr, tmp_dir, outvalue=0, datatype=None,
                      vec_epsg=None):
    """
    This function masks the input image using a polygon vector file.

    :param input_img: Input Image file.
    :param output_img: Output Image file.
    :param gdalformat: Output image file format.
    :param roi_vec_file: The input vector file.
    :param roi_vec_lyr: The name of the input layer.
    :param tmp_dir: a temporary directory for files generated during processing.
    :param outvalue: The output value in the regions masked.
    :param datatype: Output image data type. If None then the datatype of the input image will be used.
    :param vec_epsg: If projection is poorly defined by the vector layer then it can be specified.

    """
    import rsgislib
    import rsgislib.vectorutils
    import rsgislib.tools.geometrytools
    import rsgislib.tools.utils
    import rsgislib.tools.filetools

    # Does the input image BBOX intersect the BBOX of the ROI vector?
    if vec_epsg is None:
        vec_epsg = rsgislib.vectorutils.getProjEPSGFromVec(roi_vec_file, roi_vec_lyr)
    img_epsg = get_epsg_proj_from_image(input_img)
    if img_epsg == vec_epsg:
        img_bbox = get_image_bbox(input_img)
        projs_match = True
    else:
        img_bbox = get_image_bbox_in_proj(input_img, vec_epsg)
        projs_match = False
    vec_bbox = rsgislib.vectorutils.getVecLayerExtent(roi_vec_file, roi_vec_lyr, computeIfExp=True)

    if rsgislib.tools.geometrytools.do_bboxes_intersect(img_bbox, vec_bbox):
        uid_str = rsgislib.tools.utils.uid_generator()
        base_vmsk_img = rsgislib.tools.filetools.get_file_basename(input_img)

        tmp_file_dir = os.path.join(tmp_dir, "{}_{}".format(base_vmsk_img, uid_str))
        if not os.path.exists(tmp_file_dir):
            os.mkdir(tmp_file_dir)

        # Rasterise the vector layer to the input image extent.
        mem_ds, mem_lyr = rsgislib.vectorutils.getMemVecLyrSubset(roi_vec_file, roi_vec_lyr, img_bbox)

        if not projs_match:
            mem_result_ds, mem_result_lyr = rsgislib.vectorutils.reproj_vec_lyr(mem_lyr, 'mem_vec', img_epsg,
                                                                                out_vec_drv='MEMORY', out_lyr_name=None,
                                                                                in_epsg=None, print_feedback=True)
            mem_ds = None
        else:
            mem_result_ds = mem_ds
            mem_result_lyr = mem_lyr

        roi_img = os.path.join(tmp_file_dir, "{}_roiimg.kea".format(base_vmsk_img))
        rsgislib.imageutils.create_copy_img(input_img, roi_img, 1, 0, 'KEA', rsgislib.TYPE_8UINT)
        rsgislib.vectorutils.rasteriseVecLyrObj(mem_result_lyr, roi_img, burnVal=1, vecAtt=None, calcstats=True,
                                                thematic=True, nodata=0)
        mem_result_ds = None

        if datatype == None:
            datatype = rsgislib.get_gdal_data_type_from_img(input_img)
        rsgislib.imageutils.mask_img(input_img, roi_img, output_img, gdalformat, datatype, outvalue, 0)
        shutil.rmtree(tmp_file_dir)
    else:
        raise Exception("The vector file and image file do not intersect.")


def create_valid_mask(imgBandInfo, out_msk_file, gdalformat, tmpdir):
    """
    A function to create a single valid mask from the intersection of the valid masks for all the input
    images.

    :param imgBandInfo: A list of rsgislib.imageutils.ImageBandInfo objects to define the images and and bands of interest.
    :param out_msk_file: A output image file and path
    :param gdalformat: The output file format.
    :param tmpdir: A directory for temporary outputs created during the processing.

    """
    import rsgislib.tools.utils
    import rsgislib.tools.filetools
    if len(imgBandInfo) == 1:
        no_data_val = get_image_no_data_value(imgBandInfo[0].file_name)
        rsgislib.imageutils.gen_valid_mask(imgBandInfo[0].file_name, out_msk_file, gdalformat, no_data_val)
    else:
        uid_str = rsgislib.tools.utils.uid_generator()
        tmp_lcl_dir = os.path.join(tmpdir, "create_valid_mask_{}".format(uid_str))
        if not os.path.exists(tmp_lcl_dir):
            os.makedirs(tmp_lcl_dir)

        validMasks = []
        for imgInfo in imgBandInfo:
            tmpBaseName = rsgislib.tools.filetools.get_file_basename(imgInfo.file_name)
            vdmskFile = os.path.join(tmp_lcl_dir, '{}_vmsk.kea'.format(tmpBaseName))
            no_data_val = get_image_no_data_value(imgInfo.file_name)
            rsgislib.imageutils.gen_valid_mask(imgInfo.file_name, vdmskFile, gdalformat='KEA', nodata=no_data_val)
            validMasks.append(vdmskFile)

        rsgislib.imageutils.gen_valid_mask(validMasks, out_msk_file, gdalformat, nodata=0.0)
        shutil.rmtree(tmp_lcl_dir)


def get_image_pxl_values(image, band, x_coords, y_coords):
    """
    Function which gets pixel values from a image for specified
    image pixels. The coordinate space is image pixels, i.e.,
    (0 - xSize) and (0 - ySize).

    :param image: The input image name and path
    :param band: The band within the input image.
    :param x_coords: A numpy array of image X coordinates (in the image pixel coordinates)
    :param y_coords: A numpy array of image Y coordinates (in the image pixel coordinates)
    :return: An array of image pixel values.
    
    """
    from osgeo import gdal
    import tqdm
    import numpy

    if x_coords.shape[0] != y_coords.shape[0]:
        raise Exception("The X and Y image coordinates are not the same.")

    image_ds = gdal.Open(image, gdal.GA_Update)
    if image_ds is None:
        raise Exception("Could not open the input image file: '{}'".format(image))
    image_band = image_ds.GetRasterBand(band)
    if image_band is None:
        raise Exception("The image band wasn't opened")

    out_pxl_vals = numpy.zeros(x_coords.shape[0], dtype=float)

    img_data = image_band.ReadAsArray()
    for i in tqdm.tqdm(range(x_coords.shape[0])):
        out_pxl_vals[i] = img_data[y_coords[i], x_coords[i]]
    image_ds = None
    return out_pxl_vals


def set_image_pxl_values(image, band, x_coords, y_coords, pxl_value=1):
    """
    A function which sets defined image pixels to a value.
    The coordinate space is image pixels, i.e.,
    (0 - xSize) and (0 - ySize).

    :param image: The input image name and path
    :param band: The band within the input image.
    :param x_coords: A numpy array of image X coordinates (in the image pixel coordinates)
    :param y_coords: A numpy array of image Y coordinates (in the image pixel coordinates)
    :param pxl_value: The value to set the image pixel to (specified by the x/y coordinates)

    """
    from osgeo import gdal
    import tqdm

    if x_coords.shape[0] != y_coords.shape[0]:
        raise Exception("The X and Y image coordinates are not the same.")

    image_ds = gdal.Open(image, gdal.GA_Update)
    if image_ds is None:
        raise Exception("Could not open the input image file: '{}'".format(image))
    image_band = image_ds.GetRasterBand(band)
    if image_band is None:
        raise Exception("The image band wasn't opened")

    img_data = image_band.ReadAsArray()
    for i in tqdm.tqdm(range(x_coords.shape[0])):
        img_data[y_coords[i], x_coords[i]] = pxl_value
    image_band.WriteArray(img_data)
    image_ds = None


def assign_random_pxls(input_img, output_img, n_pts, img_band=1, gdalformat='KEA', edge_pxl=0, use_no_data=True,
                       seed=None):
    """
    A function which can generate a set of random pixels. Can honor the image no data value
    and use an edge buffer so pixels are not identified near the image edge.

    :param input_img: The input image providing the reference area and no data value.
    :param output_img: The output image with the random pixels.
    :param n_pts: The number of pixels to be sampled.
    :param img_band: The image band from the input image used for the no data value.
    :param gdalformat: The file format of the output image.
    :param edge_pxl: The edge pixel buffer, in pixels. This is a buffer around the edge of
                     the image within which pixels will not be identified. (Default: 0)
    :param use_no_data: A boolean specifying whether the image no data value should be used. (Default: True)
    :param seed: A random seed for generating the pixel locations. If None then a different
                 seed is used each time the system is executed. (Default None)

    Example::

        input_img = 'LS5TM_20000108_latn531lonw37_r23p204_osgb_clouds_up.kea'
        output_img = 'LS5TM_20000108_latn531lonw37_r23p204_osgb_samples.kea'
        n_pts = 5000

        assign_random_pxls(input_img, output_img, n_pts, img_band=1, gdalformat='KEA')
        # Calculate the image stats and pyramids for display
        import rsgislib.rastergis
        rsgislib.rastergis.pop_rat_img_stats(output_img, True, True, True)

    """
    import numpy
    import numpy.random

    if seed is not None:
        numpy.random.seed(seed)

    if edge_pxl < 0:
        raise Exception("edge_pxl value must be greater than 0.")

    xSize, ySize = get_image_size(input_img)

    x_min = edge_pxl
    x_max = xSize - edge_pxl

    y_min = edge_pxl
    y_max = ySize - edge_pxl

    if use_no_data:
        no_data_val = get_image_no_data_value(input_img, img_band)

        out_x_coords = numpy.zeros(n_pts, dtype=numpy.uint16)
        out_y_coords = numpy.zeros(n_pts, dtype=numpy.uint16)

        out_n_pts = 0
        pts_size = n_pts
        while out_n_pts < n_pts:
            x_coords = numpy.random.randint(x_min, high=x_max, size=pts_size, dtype=numpy.uint16)
            y_coords = numpy.random.randint(y_min, high=y_max, size=pts_size, dtype=numpy.uint16)
            pxl_vals = get_image_pxl_values(input_img, img_band, x_coords, y_coords)

            for i in range(pts_size):
                if pxl_vals[i] != no_data_val:
                    out_x_coords[out_n_pts] = x_coords[i]
                    out_y_coords[out_n_pts] = y_coords[i]
                    out_n_pts += 1
            pts_size = n_pts - out_n_pts
    else:
        out_x_coords = numpy.random.randint(x_min, high=x_max, size=n_pts, dtype=numpy.uint16)
        out_y_coords = numpy.random.randint(y_min, high=y_max, size=n_pts, dtype=numpy.uint16)

    rsgislib.imageutils.create_copy_img(input_img, output_img, 1, 0, gdalformat, rsgislib.TYPE_8UINT)
    set_image_pxl_values(output_img, 1, out_x_coords, out_y_coords, 1)


def check_img_lst(imglst, exp_x_res, exp_y_res, bbox=None, print_errors=True, abs_res=True):
    """
    A function which checks a list of images to ensure they resolution and optionally
    the bounding box is as expected.

    :param imglst: a list of input images
    :param exp_x_res: the expected image resolution in the x-axis
    :param exp_y_res: the expected image resolution in the y-axis
    :param bbox: a bbox (MinX, MaxX, MinY, MaxY) where intersection will be tested. Default None and ignored.
    :param print_errors: if True then images with errors will be printed to the console. Default: True
    :return: a list of images which have passed resolution and optional bbox intersection test.

    """
    import rsgislib.tools.geometrytools
    if abs_res:
        exp_x_res = abs(exp_x_res)
        exp_y_res = abs(exp_y_res)
    out_imgs = list()
    for img in imglst:
        img_res = get_image_res(img, abs_vals=abs_res)
        if bbox is not None:
            img_bbox = get_image_bbox(img)
        if (img_res[0] != exp_x_res) or (img_res[1] != exp_y_res):
            if print_errors:
                print("{} has resolution: {}".format(img, img_res))
        elif (bbox is not None) and (not rsgislib.tools.geometrytools.bbox_intersection(bbox, img_bbox)):
            if print_errors:
                print("{} has BBOX: {}".format(img, img_bbox))
        else:
            out_imgs.append(img)
    return out_imgs


def check_img_file_comparison(base_img, comp_img, test_n_bands=False, test_eql_bbox=False, print_errors=True):
    """
    A function which tests whether an image is comparable:
     * Image resolution
     * Intersecting bounding box
     * Optionally the number of bands
     * Optionally whether the BBOXs match rather than intersect

    :param base_img: base input image which will be compared to
    :param comp_img: the input image which will be compared to the base.
    :param test_n_bands: if true the number of image bands will be checked (i.e., the same)
    :parma test_eql_bbox: if true then the bboxes will need to be identical between the images.
    :param print_errors: if True then images with errors will be printed to the console. Default: True
    :return: Boolean (True; images are compariable)

    """
    import rsgislib.tools.geometrytools
    imgs_match = True

    if not do_image_res_match(base_img, comp_img):
        if print_errors:
            base_img_res = get_image_res(base_img)
            comp_img_res = get_image_res(comp_img)
            print("Base Image Res: {}".format(base_img_res))
            print("Comp Image Res: {}".format(comp_img_res))
        imgs_match = False

    base_img_bbox = get_image_bbox(base_img)
    comp_img_bbox = get_image_bbox(comp_img)
    if not rsgislib.tools.geometrytools.bbox_intersection(base_img_bbox, comp_img_bbox):
        if print_errors:
            print("Base Image BBOX: {}".format(base_img_bbox))
            print("Comp Image BBOX: {}".format(comp_img_bbox))
        imgs_match = False

    if test_eql_bbox:
        if not rsgislib.tools.geometrytools.bbox_equal(base_img_bbox, comp_img_bbox):
            if print_errors:
                print("Base Image BBOX: {}".format(base_img_bbox))
                print("Comp Image BBOX: {}".format(comp_img_bbox))
            imgs_match = False

    if test_n_bands:
        base_img_nbands = get_image_band_count(base_img)
        comp_img_nbands = get_image_band_count(comp_img)
        if base_img_nbands != comp_img_nbands:
            if print_errors:
                print("Base Image n-bands: {}".format(base_img_nbands))
                print("Comp Image n-bands: {}".format(comp_img_nbands))
            imgs_match = False

    return imgs_match


def test_img_lst_intersects(imgs, stop_err=False):
    """
    A function which will test a list of image to check if they intersect, have matching image
    resolution and projection. The first image in the list is used as the reference to which all
    others are compared to.

    :param imgs: list of images file paths
    :param stop_err: boolean. Default: False.
                     If True then an exception will be thrown if error found.
                     If False then errors will just be printed to screen.

    """
    import rsgislib.tools.geometrytools
    first = True
    for img in imgs:
        print(img)
        img_bbox = get_image_bbox(img)
        img_proj = get_epsg_proj_from_image(img)
        img_res = get_image_res(img)
        if first:
            first = False
            ref_img = img
            ref_bbox = img_bbox
            ref_proj = img_proj
            ref_res = img_res
            print("\tReference Image")
        else:
            if ref_proj != img_proj:
                print("\tProjection does not match the reference (i.e., first image)")
                print("\tRef (first) Image: {}".format(ref_img))
                print("\tRef (first) EPSG: {}".format(ref_proj))
                print("\tImage: {}".format(img))
                print("\tImage EPSG: {}".format(img_proj))
                if stop_err:
                    raise Exception("Projection does not match the reference (i.e., first image)")
            elif not rsgislib.tools.geometrytools.do_bboxes_intersect(ref_bbox, img_bbox):
                print("\tBBOX does not intersect the reference (i.e., first image)")
                print("\tRef (first) Image: {}".format(ref_img))
                print("\tRef (first) BBOX:", ref_bbox)
                print("\tImage: {}".format(img))
                print("\tImage BBOX: ", img_bbox)
                if stop_err:
                    raise Exception("BBOX does not intersect the reference (i.e., first image)")
            elif (img_res[0] != ref_res[0]) or (img_res[1] != ref_res[1]):
                print("\tImage resolution does not match the reference (i.e., first image)")
                print("\tRef (first) Image: {}".format(ref_img))
                print("\tRef (first) Res: ", ref_res)
                print("\tImage: {}".format(img))
                print("\tImage Res: ", img_res)
                if stop_err:
                    raise Exception("Image resolution does not match the reference (i.e., first image)")
            else:
                print("\tOK")


def whiten_image(input_img, valid_msk_img, valid_msk_val, output_img, gdalformat):
    """
    A function which whitens the input image where the noise covariance matrix is
    used to decorrelate and rescale the noise in the data (noise whitening).
    This results in a transformed datset in which the noise has unit variance
    and no band-to-band correlations. The valid mask is used to identify the
    areas of valid data. This function is used to an MNF transformation.

    WARNING: This function loads the whole image into memory and therefore
             can use a lot of memory for the analysis.

:param input_img: the input image
:param valid_msk_img: a valid input image mask
:param valid_msk_val: the pixel value in the mask image specifying valid image pixels.
:param output_img: the output image file name and path (will be same dimensions as the input)
:param gdalformat: the GDAL image file format of the output image file.

"""
    import osgeo.gdal as gdal
    import rsgislib.imageutils
    import tqdm
    import numpy

    def _cov(M):
        """
        Compute the sample covariance matrix of a 2D matrix.

        Parameters:
          M: `numpy array`
            2d matrix of HSI data (N x p)

        Returns: `numpy array`
            sample covariance matrix
        """
        N = M.shape[0]
        u = M.mean(axis=0)
        M = M - numpy.kron(numpy.ones((N, 1)), u)
        C = numpy.dot(M.T, M) / (N - 1)
        return C

    def _whiten(M):
        """
        Whitens a HSI cube. Use the noise covariance matrix to decorrelate
        and rescale the noise in the data (noise whitening).
        Results in transformed data in which the noise has unit variance
        and no band-to-band correlations.

        Parameters:
            M: `numpy array`
                2d matrix of HSI data (N x p).

        Returns: `numpy array`
            Whitened HSI data (N x p).

        Reference:
            Krizhevsky, Alex, Learning Multiple Layers of Features from
            Tiny Images, MSc thesis, University of Toronto, 2009.
            See Appendix A.
        """
        sigma = _cov(M)
        U, S, V = numpy.linalg.svd(sigma)
        S_1_2 = S ** (-0.5)
        S = numpy.diag(S_1_2.T)
        Aw = numpy.dot(V, numpy.dot(S, V.T))
        return numpy.dot(M, Aw)

    imgMskDS = gdal.Open(valid_msk_img)
    if imgMskDS is None:
        raise Exception("Could not open valid mask image")
    n_msk_bands = imgMskDS.RasterCount
    x_msk_size = imgMskDS.RasterXSize
    y_msk_size = imgMskDS.RasterYSize

    if n_msk_bands != 1:
        raise Exception("Valid mask only expected to have a single band.")

    imgMskBand = imgMskDS.GetRasterBand(1)
    if imgMskBand is None:
        raise Exception("Could not open image band (1) in valid mask")

    vld_msk_band_arr = imgMskBand.ReadAsArray().flatten()
    imgMskDS = None

    imgDS = gdal.Open(input_img)
    if imgDS is None:
        raise Exception("Could not open input image")
    n_bands = imgDS.RasterCount
    x_size = imgDS.RasterXSize
    y_size = imgDS.RasterYSize

    if x_msk_size != x_size:
        raise Exception("Mask and input image size in the x axis do not match.")

    if y_msk_size != y_size:
        raise Exception("Mask and input image size in the y axis do not match.")

    img_data = numpy.zeros((n_bands, (x_size * y_size)), dtype=numpy.float32)

    print("Importing Bands:")
    for n in tqdm.tqdm(range(n_bands)):
        imgBand = imgDS.GetRasterBand(n + 1)
        if imgBand is None:
            raise Exception("Could not open image band ({})".format(n + 1))
        no_data_val = imgBand.GetNoDataValue()
        band_arr = imgBand.ReadAsArray().flatten()
        band_arr = band_arr.astype(numpy.float32)
        img_data[n] = band_arr
    imgDS = None
    band_arr = None

    img_data = img_data.T
    pxl_idxs = numpy.arange(vld_msk_band_arr.shape[0])
    pxl_idxs = pxl_idxs[vld_msk_band_arr == valid_msk_val]
    img_data = img_data[vld_msk_band_arr == valid_msk_val]

    img_flat_white = _whiten(img_data)

    print("Create empty output image file")
    rsgislib.imageutils.create_copy_img(input_img, output_img, n_bands, 0, gdalformat, rsgislib.TYPE_32FLOAT)

    # Open output image
    outImgDS = gdal.Open(output_img, gdal.GA_Update)
    if outImgDS is None:
        raise Exception("Could not open output image")

    out_data_band = numpy.zeros_like(vld_msk_band_arr, dtype=numpy.float32)

    print("Output Bands:")
    for n in tqdm.tqdm(range(n_bands)):
        out_data_band[...] = 0.0
        out_data_band[pxl_idxs] = img_flat_white[..., n]
        out_img_data = out_data_band.reshape((y_size, x_size))
        outImgBand = outImgDS.GetRasterBand(n + 1)
        if outImgBand is None:
            raise Exception("Could not open output image band (1)")
        outImgBand.WriteArray(out_img_data)
        outImgBand = None
    outImgDS = None


def spectral_smoothing(input_img, valid_msk_img, valid_msk_val, output_img, win_len=5, polyorder=3, gdalformat='KEA',
                       datatype=rsgislib.TYPE_32FLOAT, calc_stats=True):
    """
    This function performs spectral smoothing using a Savitzky-Golay filter.
    Typically applied to hyperspectral data to remove noise.

    :param input_img: input image file.
    :param valid_msk_img: an image file representing the valid data region
    :param valid_msk_val: image pixel value in the mask for the valid data region
    :param output_img: the output image file
    :param win_len: the window length for the Savitzky-Golay filter (Default: 5)
    :param polyorder: the order of the polynomial for the Savitzky-Golay filter (Default: 3)
    :param gdalformat: the output file format. (Default: KEA)
    :param datatype: the output image datatype (Default: Float 32)
    :param calc_stats: Boolean specifying whether to calculate pyramids and metadata stats (Default: True)

    """
    from rios import applier
    import numpy
    import scipy.signal
    import rsgislib.imageutils

    try:
        import tqdm
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress
        progress_bar = cuiprogress.GDALProgressBar()

    np_dtype = rsgislib.get_numpy_datatype(datatype)
    in_no_date = rsgislib.get_image_no_data_value(input_img)

    infiles = applier.FilenameAssociations()
    infiles.image = input_img
    infiles.valid_msk = valid_msk_img
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = output_img
    otherargs = applier.OtherInputs()
    otherargs.valid_msk_val = valid_msk_val
    otherargs.win_len = win_len
    otherargs.polyorder = polyorder
    otherargs.in_no_date = in_no_date
    otherargs.np_dtype = np_dtype
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = True
    aControls.calcStats = False

    def _applySmoothing(info, inputs, outputs, otherargs):
        if numpy.any(inputs.valid_msk == otherargs.valid_msk_val):
            img_flat = numpy.moveaxis(inputs.image, 0, 2).reshape(-1, inputs.image.shape[0])

            ID = numpy.arange(img_flat.shape[0])
            n_feats = ID.shape[0]

            ID = ID[inputs.valid_msk.flatten() == otherargs.valid_msk_val]
            img_flat = img_flat[inputs.valid_msk.flatten() == otherargs.valid_msk_val]

            img_flat_smooth = scipy.signal.savgol_filter(img_flat, otherargs.win_len, otherargs.polyorder, axis=1)

            img_flat_smooth_arr = numpy.zeros([n_feats, inputs.image.shape[0]], dtype=otherargs.np_dtype)
            img_flat_smooth_arr[...] = in_no_date
            img_flat_smooth_arr[ID] = img_flat_smooth

            out_arr = img_flat_smooth_arr.reshape(inputs.image.shape[1], inputs.image.shape[2], inputs.image.shape[0])
            out_arr = numpy.moveaxis(out_arr, 2, 0)
            outputs.outimage = out_arr
        else:
            outputs.outimage = numpy.zeros_like(inputs.image, dtype=otherargs.np_dtype)

    applier.apply(_applySmoothing, infiles, outfiles, otherargs, controls=aControls)

    if calc_stats:
        rsgislib.imageutils.pop_img_stats(output_img, usenodataval=True, nodataval=in_no_date, calcpyramids=True)


def calc_wsg84_pixel_size(img, out_img, gdalformat='KEA'):
    """
A function which calculates the x and y pixel resolution (in metres) of each pixel projected in WGS84.

:param img: input image, for which the per-pixel area will be calculated.
:param out_img: output image file.

"""
    import rsgislib.tools
    from rios import applier
    import numpy

    try:
        import tqdm
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress
        progress_bar = cuiprogress.GDALProgressBar()

    x_res, y_res = get_image_res(img, abs_vals=True)

    infiles = applier.FilenameAssociations()
    infiles.img = img
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = out_img
    otherargs = applier.OtherInputs()
    otherargs.x_res = x_res
    otherargs.y_res = y_res
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = False
    aControls.calcStats = False

    def _calcPixelRes(info, inputs, outputs, otherargs):
        xBlock, yBlock = info.getBlockCoordArrays()

        x_res_arr = numpy.zeros_like(yBlock, dtype=float)
        x_res_arr[...] = otherargs.x_res
        y_res_arr = numpy.zeros_like(yBlock, dtype=float)
        y_res_arr[...] = otherargs.y_res
        x_res_arr_m, y_res_arr_m = rsgislib.tools.degrees_to_metres(yBlock, x_res_arr, y_res_arr)
        outputs.outimage = numpy.stack((x_res_arr_m, y_res_arr_m), axis=0)

    applier.apply(_calcPixelRes, infiles, outfiles, otherargs, controls=aControls)


def mask_all_band_zero_vals(input_img, output_img, gdalformat, out_val=1):
    """
Function which identifies image pixels which have a value of zero
all bands which are defined as true 'no data' regions while other
pixels have a value of zero or less then zero for one or few pixels
which causes confusion between valid data pixel and no data pixels.
This function will identify and define those pixels which are valid
but with a value <= 0 for isolate bands to a new output value (out_val).

This function might be used for surface reflectance data where the
atmospheric correction has resulted in value <=0 which isn't normally
possible and where 0 is commonly used as a no data value. In this case
setting those pixel band values to 1 (if data has been multiplied by
100, 1000, or 10000, for example) or a small fraction (e.g., 0.001) if
values are between 0-1.

:param input_img: the input image
:param output_img: the output image file name and path
:param gdalformat: the GDAL image file format of the output image file.
:param out_val: Output pixel band value (default: 1)

"""
    from rios import applier
    import numpy

    try:
        import tqdm
        progress_bar = rsgislib.TQDMProgressBar()
    except:
        from rios import cuiprogress
        progress_bar = cuiprogress.GDALProgressBar()

    infiles = applier.FilenameAssociations()
    infiles.image = input_img
    outfiles = applier.FilenameAssociations()
    outfiles.outimage = output_img
    otherargs = applier.OtherInputs()
    otherargs.out_val = out_val
    aControls = applier.ApplierControls()
    aControls.progress = progress_bar
    aControls.drivername = gdalformat
    aControls.omitPyramids = True
    aControls.calcStats = False

    def _applyzeronodata(info, inputs, outputs, otherargs):
        """
        This is an internal rios function
        """
        img_sum = numpy.sum(inputs.image, axis=0)
        vld_msk = img_sum > 0
        outputs.outimage = inputs.image
        outputs.outimage[(inputs.image <= 0) & vld_msk] = otherargs.out_val

    applier.apply(_applyzeronodata, infiles, outfiles, otherargs, controls=aControls)


