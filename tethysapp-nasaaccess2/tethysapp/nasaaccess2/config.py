import os
from .app import nasaaccess2


working_dir = nasaaccess2.get_custom_setting('Working Directory')

data_path= working_dir + 'data/'
nasaaccess_script = data_path + 'nasaaccess.py'
nasaaccess_log = data_path + 'nasaaccess.log'

python_path = nasaaccess2.get_custom_setting("Nasa Access Conda Environment Path")
nasaaccess_py3 = os.path.join(python_path)

geoserver = {
    'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
    'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
    'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
    'user':'admin',
    'password':'geoserver',
    'workspace':'nasaaccess',
    'URI': 'nasaaccess'
}