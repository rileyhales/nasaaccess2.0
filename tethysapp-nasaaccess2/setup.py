import os
import sys
from setuptools import setup, find_packages
from tethys_apps.app_installation import custom_develop_command, custom_install_command

### Apps Definition ###
app_package = 'nasaaccess2'
release_package = 'tethysapp-' + app_package
app_class = 'nasaaccess2.app:Nasaaccess2'
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)

### Python Dependencies ###
dependencies = ['numpy', 'scipy', 'pandas', 'geopandas', 'xarray', 'rasterio', 'shapely', 'requests', 'georaster', 'netcdf4', 'gdal']

setup(
    name=release_package,
    version='0.0.1',
    tags='',
    description='An application that accepts shapefiles and DEM data for a watershed and prepares a SWAT model',
    long_description='',
    keywords='SWAT',
    author='Spencer McDonald, Riley Hales',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    cmdclass={
        'install': custom_install_command(app_package, app_package_dir, dependencies),
        'develop': custom_develop_command(app_package, app_package_dir, dependencies)
    }
)
