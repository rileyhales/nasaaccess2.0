import os

data_path = os.path.dirname(__file__)
nasaaccess_log = os.path.join(data_path, 'workspaces/app_workspace/nasaaccess.log')
nasaaccess_script = os.path.join(data_path, 'nasaaccess.py')

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
