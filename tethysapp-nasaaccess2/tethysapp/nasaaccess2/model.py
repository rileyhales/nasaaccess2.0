from django.db import models
import os, random, string, subprocess
from .config import data_path, temp_path
from tethys_sdk.services import get_spatial_dataset_engine
import logging
from pwd import getpwnam

logging.basicConfig(filename='/home/ubuntu/nasaaccess_data/nasaaccess.log',level=logging.INFO)


# Model for the Upload Shapefiles form
class Shapefiles(models.Model):
    shapefile = models.FileField(upload_to='nasaaccess_data/shapefiles')

# Model for the Upload DEM files form
class DEMfiles(models.Model):
    DEMfile = models.FileField(upload_to='nasaaccess_data/DEMfiles/')

# Model for data access form
class accessCode(models.Model):
    access_code = models.CharField(max_length=6)


def nasaaccess_run(email, functions, watershed, dem, start, end):
    #identify where each of the input files are located in the server
    shp_path = os.path.join(data_path, 'shapefiles', watershed, watershed + '.shp')
    dem_path = os.path.join(data_path, 'DEMfiles', dem + '.tif')
    #create a new folder to store the user's requested data
    unique_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    unique_path = os.path.join(data_path, 'outputs', unique_id)
    os.makedirs(unique_path)
    os.chmod(unique_path, 0o777)
    unique_path = os.path.join(unique_path, 'nasaaccess_data')
    os.makedirs(unique_path)
    os.chmod(unique_path, 0o777)
    os.chown(unique_path, 1000, 1000)
    #create a temporary directory to store all intermediate data while nasaaccess functions run
    tempdir = os.path.join(temp_path, unique_id)
    os.makedirs(tempdir)
    os.chmod(tempdir, 0o777)
    os.chown(tempdir, 1000, 1000)


    functions = ','.join(functions)

    try:
        logging.info("trying to run nasaaccess functions")
        #pass user's inputs and file paths to the nasaaccess python function that will run detached from the app
        run = subprocess.call(["/home/ubuntu/tethys/miniconda/envs/nasaaccess/bin/python3", "/home/ubuntu/subprocesses/nasaaccess.py", email, functions, unique_id,
                                shp_path, dem_path, unique_path, tempdir, start, end])

        return "nasaaccess is running"
    except Exception as e:
        logging.info(str(e))
        return str(e)

def upload_shapefile(id):

    '''
    Check to see if shapefile is on geoserver. If not, upload it.
    '''
    WORKSPACE = 'nasaaccess'
    GEOSERVER_URI = 'http://www.example.com/nasaaccess'

    geoserver_engine = get_spatial_dataset_engine(name='default')
    response = geoserver_engine.get_layer(id, debug=True)
    if response['success'] == False:
        print('Shapefile was not found on geoserver. Uploading it now from app workspace')

        #Create the workspace if it does not already exist
        response = geoserver_engine.list_workspaces()
        if response['success']:
            workspaces = response['result']
            if WORKSPACE not in workspaces:
                geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)

        #Create a string with the path to the zip archive
        zip_archive = os.path.join(data_path, 'shapefiles', id + '.zip')

        # Upload shapefile to the workspaces
        store = id
        store_id = WORKSPACE + ':' + store
        geoserver_engine.create_shapefile_resource(
            store_id=store_id,
            shapefile_zip=zip_archive,
            overwrite=True
        )
       
# request_url = '{0}workspaces/{1}/datastores/{2}/file.shp'.format(geoserver['rest_url'],
#                                                                                  geoserver['workspace'], storename)
#
# requests.put(request_url, verify=False, headers=headers, data=data, auth=(user, password))
