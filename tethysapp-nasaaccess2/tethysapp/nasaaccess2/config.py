import os
from .app import nasaaccess2

data_path = os.path.join('home/ubuntu/nasaaccess_data')

temp_path = os.path.join('home/ubuntu/tethys_temp/nasaaccess')

geoserver = {'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
             'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
             'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
             'user':'admin',
             'password':'geoserver',
             'workspace':'nasaaccess',
             'URI': 'nasaaccess'}

