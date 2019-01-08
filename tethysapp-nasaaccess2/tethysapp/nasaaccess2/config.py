import os
from .app import nasaaccess2


data_path = os.path.dirname(__file__)
nasaaccess_log = os.path.join(data_path, 'workspaces/app_workspace/nasaaccess.log')
nasaaccess_script = os.path.join(data_path, 'nasaaccess.py')

# python_path = nasaaccess2.get_custom_setting("Nasa Access Conda Environment Path")
# nasaaccess_py3 = os.path.join(python_path)
nasaaccess_py3 = ''


geoserver = {
    'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
    'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
    'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
    'user':'admin',
    'password':'geoserver',
    'workspace':'nasaaccess',
    'URI': 'nasaaccess'
}