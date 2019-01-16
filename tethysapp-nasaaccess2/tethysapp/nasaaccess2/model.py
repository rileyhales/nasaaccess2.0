from django.db import models
import os, random, string, requests, shutil, logging, zipfile
from .config import *
from tethys_sdk.services import get_spatial_dataset_engine

import threading
from .nasaaccess import nasaaccess_controller

logging.basicConfig(filename=nasaaccess_log, level=logging.INFO)


# Model for the Upload Shapefiles form
class Shapefiles(models.Model):
    shapefile = models.FileField(upload_to='workspaces/app_workspace/temp/shapefiles', max_length=500)


# Model for the Upload DEM files form
class DEMfiles(models.Model):
    DEMfile = models.FileField(upload_to='workspaces/app_workspace/temp/DEMfiles', max_length=500)


# Model for data access form
class accessCode(models.Model):
    access_code = models.CharField(max_length=6)


def upload_shapefile(id, shp_path):

    """
    Check to see if shapefile is on geoserver. If not, upload it.
    """

    # Create a string with the path to the zip archive
    zip_archive = os.path.join(data_path, 'temp', 'shapefiles', id + '.zip')
    zip_ref = zipfile.ZipFile(zip_archive, 'r')
    zip_ref.extractall(shp_path)
    zip_ref.close()

    prj_path = os.path.join(shp_path, id + '.prj')
    f = open(prj_path)
    validate = 0
    for line in f:
        if 'PROJCS' in line:
            validate = 1
            print('This shapefile is in a projected coordinate system. You must use a geographic coordinate system')

    if validate == 0:
        geoserver_engine = get_spatial_dataset_engine(name='ADPC')
        response = geoserver_engine.get_layer(id, debug=True)

        WORKSPACE = geoserver['workspace']
        GEOSERVER_URI = geoserver['URI']

        if response['success'] == False:
            print('Shapefile was not found on geoserver. Uploading it now from app workspace')

            # Create the workspace if it does not already exist
            response = geoserver_engine.list_workspaces()
            if response['success']:
                workspaces = response['result']
                if WORKSPACE not in workspaces:
                    geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)

            # Upload shapefile to the workspaces
            store = id
            store_id = WORKSPACE + ':' + store
            geoserver_engine.create_shapefile_resource(
                store_id=store_id,
                shapefile_zip=zip_archive,
                overwrite=True
            )
    os.remove(zip_archive)


def upload_dem(id, dem_path):

    """
    upload dem to user workspace and geoserver
    """

    shutil.copy2(os.path.join(data_path, 'temp', 'DEMfiles', id), dem_path)

    geoserver_engine = get_spatial_dataset_engine(name='ADPC')
    response = geoserver_engine.get_layer(id, debug=True)

    WORKSPACE = geoserver['workspace']
    GEOSERVER_URI = geoserver['URI']

    if response['success'] == False:
        print('DEM was not found on geoserver. Uploading it now from app workspace')

        # Create the workspace if it does not already exist
        response = geoserver_engine.list_workspaces()
        if response['success']:
            workspaces = response['result']
            if WORKSPACE not in workspaces:
                geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)

        file_path = os.path.join(dem_path, id)
        storename = id
        headers = {'Content-type': 'image/tiff', }
        user = geoserver['user']
        password = geoserver['password']
        data = open(file_path, 'rb').read()

        request_url = '{0}workspaces/{1}/coveragestores/{2}/file.geotiff'.format(geoserver['rest_url'],
                                                                                 WORKSPACE, storename)

        requests.put(request_url, verify=False, headers=headers, data=data, auth=(user, password))
    os.remove(os.path.join(data_path, 'temp', 'DEMfiles', id))