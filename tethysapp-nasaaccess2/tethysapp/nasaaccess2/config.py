import os
from .app import nasaaccess2

data_path = os.path.join(nasaaccess2.get_app_workspace().path)

temp_path = os.path.join(nasaaccess2.get_app_workspace().path, 'temp')

geoserver = {'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
             'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
             'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
             'user':'admin',
             'password':'geoserver',
             'workspace':'nasaaccess',
             'URI': 'nasaaccess'}

