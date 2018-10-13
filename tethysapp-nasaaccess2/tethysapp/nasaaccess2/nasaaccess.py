from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, sys, os, time
import numpy as np
import shapely
import rasterio
import rasterio.mask
import netCDF4
import pandas as pd
import datetime
import geopandas as gpd
import georaster
import requests
import os
import shutil
import xarray as xr
import warnings


#read in file paths and arguments from subprocess call in model.py
email = sys.argv[1]
functions = sys.argv[2].split(',')
unique_id = sys.argv[3]
shp_path = sys.argv[4]
dem_path = sys.argv[5]
unique_path = sys.argv[6]
tempdir = sys.argv[7]
start = sys.argv[8]
end = sys.argv[9]

#change working directory to temporary directory for storing intermediate data
os.chdir(tempdir)

time.sleep(120)

#Run nasaaccess functions requested by user
for func in functions:
    print(func)
    if func == 'GPMpolyCentroid':
        output_path = unique_path + '/GPMpolyCentroid/'
        os.makedirs(output_path, 0777)
        print('running GPMpoly')
        GPMpolyCentroid(output_path, shp_path, dem_path, start, end)
    elif func == 'GPMswat':
        output_path = unique_path + '/GPMswat/'
        os.makedirs(output_path, 0777)
        print('running GPMswat')
        GPMswat(output_path, shp_path, dem_path, start, end)
    elif func == 'GLDASpolyCentroid':
        output_path = unique_path + '/GLDASpolyCentroid/'
        os.makedirs(output_path, 0777)
        print('running GLDASpoly')
        GLDASpolyCentroid(output_path, shp_path, dem_path, start, end)
    elif func == 'GLDASwat':
        output_path = unique_path + '/GLDASwat/'
        os.makedirs(output_path, 0777)
        print('running GLDASwat')
        GLDASwat(output_path, shp_path, dem_path, start, end)

#when data is ready, send the user an email with their unique access code
send_email(email, unique_id)


def GPMswat(Dir, watershed, DEM, start, end):
    ##########Description
    # This function downloads rainfall remote sensing data of TRMM and IMERG from NASA GSFC servers, extracts data from grids within a specified watershed shapefile, and then generates tables in a format that SWAT requires for rainfall data input.
    # The function also generates the rainfall stations file input (file with columns: ID, File NAME, LAT, LONG, and ELEVATION) for those selected grids that fall within the specified watershed.

    #########Arguments

    # Dir       A directory name to store gridded rainfall and rain stations files.
    # watershed	A study watershed shapefile spatially describing polygon(s) in a geographic projection sp::CRS('+proj=longlat +datum=WGS84').
    # DEM	A study watershed digital elevation model raster in a geographic projection sp::CRS('+proj=longlat +datum=WGS84').
    # start	Begining date for gridded rainfall data.
    # end	Ending date for gridded rainfall data.

    ########Details
    # A user should visit https://disc.gsfc.nasa.gov/data-access to register with the Earth Observing System Data and Information System (NASA Earthdata) and then authorize NASA GESDISC Data Access to successfuly work with this function. The function accesses NASA Goddard Space Flight Center server address for IMERG remote sensing data products at (https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.05/), and NASA Goddard Space Flight Center server address for TRMM remote sensing data products (https://disc2.gesdisc.eosdis.nasa.gov/data/TRMM_RT/TRMM_3B42RT_Daily.7). The function uses varible name ('precipitationCal') for rainfall in IMERG data products and variable name ('precipitation') for TRMM rainfall data products. Units for gridded rainfall data are 'mm'.

    # IMERG dataset is the GPM Level 3 IMERG *Final* Daily 0.1 x 0.1 deg (GPM_3IMERGDF) derived from the half-hourly GPM_3IMERGHH. The derived result represents the final estimate of the daily accumulated precipitation. The dataset is produced at the NASA Goddard Earth Sciences (GES) Data and Information Services Center (DISC) by simply summing the valid precipitation retrievals for the day in GPM_3IMERGHH and giving the result in (mm) https://pmm.nasa.gov/data-access/downloads/gpm.

    # TRMM dataset is a daily 0.25 x 0.25 deg accumulated precipitation product that is generated from the Near Real-Time 3-hourly TMPA (3B42RT). It is produced at the NASA GES DISC, as a value added product. Simple summation of valid retrievals in a grid cell is applied for the data day. The result is given in (mm) https://pmm.nasa.gov/data-access/downloads/trmm.

    # Since IMERG data products are only available from 2014-March-12 to present, then this function uses TRMM data products for time periods earlier than 2014-March-12. Keep in mind that TRMM data products that are compatible with IMERG data products are only available from 2000-March-01. The function outputs table and gridded data files that match grid points resolution of IMERG data products (i.e., resolution of 0.1 deg). Since TRMM and IMERG data products do not have a similar spatial resolution (i.e., 0.25 and 0.1 deg respectively), the function assigns the nearest TRMM grid point to any missing IMERG data point as an approximate (i.e. during 2000-March-01 to 2014-March-11 time period).

    # The GPMswat function relies on 'curl' tool to transfer data from NASA servers to a user machine, using HTTPS supported protocol. The 'curl' command embedded in this function to fetch precipitation IMERG/TRMM netcdf daily global files is designed to work seamlessly given that appropriate logging information are stored in the ".netrc" file and the cookies file ".urs_cookies" as explained in registering with the Earth Observing System Data and Information System. It is imperative to say here that a user machine should have 'curl' installed as a prerequisite to run GPMswat.

    ########Value
    # A table that includes points ID, Point file name, Lat, Long, and Elevation information formated to be read with SWAT, and a scalar of rainfall gridded data values at each point within the study watershed in ascii format needed by SWAT model weather inputs will be stored at Dir.

    #########Note
    # start should be equal to or greater than 2000-Mar-01.

    #######Example
    # GPMswat(Dir = "./SWAT_INPUT/", watershed = "LowerMekong.shp",DEM = "LowerMekong_dem.tif", start = "2015-12-1", end = "2015-12-3")

    url_IMERG_input = 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.05/'
    url_TRMM_input = 'https://disc2.gesdisc.eosdis.nasa.gov/data/TRMM_RT/TRMM_3B42RT_Daily.7/'
    myvarIMERG = 'precipitationCal'
    myvarTRMM = 'precipitation'
    start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
    ####Before getting to work on this function do this check
    if start >= datetime.date(2000, 3, 1):
        # Constructing time series based on start and end input days!
        time_period = pd.date_range(start, end).tolist()
        # Reading cell elevation data (DEM should be in geographic projection)
        watershed_elevation = georaster.SingleBandRaster(DEM, load_data=False)
        # Reading the study Watershed shapefile
        polys = gpd.read_file(watershed)
        # extract the Watershed geometry in GeoJSON format
        geoms = polys.geometry.values  # list of shapely geometries
        geoms = [shapely.geometry.mapping(geoms[0])]
        # SWAT climate 'precipitation' master file name
        filenametableKEY = Dir + myvarTRMM + 'Master.txt'
        # The IMERG data grid information
        # Read a dummy day to extract spatial information and assign elevation data to the grids within the study watersheds
        DUMMY_DATE = datetime.date(2014, 5, 1)
        mon = DUMMY_DATE.strftime('%m')
        year = DUMMY_DATE.strftime('%Y')
        myurl = url_IMERG_input + year + '/' + mon + '/'
        check1 = requests.get(myurl)
        if check1.status_code == 200:
            filenames = check1._content
            # getting one of the daily files at the monthly URL specified by DUMMY Date
            filenames = pd.read_html(filenames)[0][1][3]
            # Extract the IMERG nc4 files for the specific date
            # trying here the first day since I am only interested on grid locations
            # downloading one file
            if not os.path.exists('./temp/'):
                os.makedirs('./temp/')
                destfile = './temp/' + filenames
                filenames = myurl + filenames
                r = requests.get(filenames, stream=True)
                with open(destfile, 'wb') as fd:
                    fd.write(r.content)
                    fd.close()
                # reading ncdf file
                nc = netCDF4.Dataset(destfile)
                # since geographic info for all files are the same (assuming we are working with the same data product)
                ###evaluate these values one time!
                ###getting the y values (longitudes in degrees east)
                nc_long_IMERG = nc.variables['lon'][:]
                ####getting the x values (latitudes in degrees north)
                nc_lat_IMERG = nc.variables['lat'][:]
                ####getting the transform and resolutions for the IMERG raster data
                xres_IMERG = (nc_long_IMERG[-1] - nc_long_IMERG[0]) / nc_long_IMERG.shape[0]
                yres_IMERG = (nc_lat_IMERG[-1] - nc_lat_IMERG[0]) / nc_lat_IMERG.shape[0]
                transform_IMERG = rasterio.transform.from_origin(west=nc_long_IMERG[0], north=nc_lat_IMERG[-1],
                                                                 xsize=xres_IMERG, ysize=yres_IMERG)
                # extract data
                data = nc.variables[myvarIMERG][:]
                # reorder the rows
                data = np.transpose(data)
                # close the netcdf file link
                nc.close()
                # save the daily climate data values in a raster
                IMERG_temp_filename = './temp/' + 'pcp_rough.tif'
                IMERG = rasterio.open(IMERG_temp_filename, 'w', driver='GTiff', height=data.shape[0],
                                      width=data.shape[1], count=1, dtype=data.dtype.name, crs=polys.crs,
                                      transform=transform_IMERG)  #
                IMERG.write(data, 1)
                IMERG.close()
                # extract the raster x,y values within the watershed (polygon)
                with rasterio.open(IMERG_temp_filename) as src:
                    out_image, out_transform = rasterio.mask.mask(src, geoms, all_touched=True, crop=True)
                # The out_image result is a Numpy masked array
                # no data values of the IMERG raster
                no_data = src.nodata
                # extract the values of the masked array
                data = out_image.data[0]
                # extract the row, columns of the valid values
                row, col = np.where(data != no_data)
                # Pcp = np.extract(data != no_data, data)
                # polys_crs_wkt = src.crs.wkt
                src.close()
                # Now get the coordinates of a cell center using affine transforms
                # Creation of a new resulting GeoDataFrame with the col, row and precipitation values
                d = gpd.GeoDataFrame({'NAME': myvarTRMM, 'col': col, 'row': row}, crs=polys.crs)  #
                # lambda for evaluating raster data at cell center
                rc2xy = lambda r, c: (c, r) * T1
                T1 = out_transform * rasterio.Affine.translation(0.5, 0.5)  # reference the pixel center
                # coordinate transformation
                d['x'] = d.apply(lambda row: rc2xy(row.row, row.col)[0], axis=1)
                d['y'] = d.apply(lambda row: rc2xy(row.row, row.col)[1], axis=1)
                # geometry
                d['geometry'] = d.apply(lambda row: shapely.geometry.Point(row['x'], row['y']), axis=1)
                study_area_records_IMERG = gpd.sjoin(d, polys, how='inner', op='intersects')
                ###working with DEM raster
                # lambda to evaluate elevation based on lat/long
                elev_x_y = lambda x, y: watershed_elevation.value_at_coords(x, y, latlon=True)
                study_area_records_IMERG['ELEVATION'] = study_area_records_IMERG.apply(
                    lambda row: elev_x_y(row.x, row.y), axis=1)
                study_area_records_IMERG = study_area_records_IMERG.reset_index()
                study_area_records_IMERG = study_area_records_IMERG.rename(
                    columns={'index': 'ID', 'x': 'LONG', 'y': 'LAT'})
                study_area_records_IMERG['NAME'] = study_area_records_IMERG['NAME'] + study_area_records_IMERG[
                    'ID'].astype(str)
                # study_area_records_IMERG.to_csv('./IMERG_Table_result.txt',index=False)#
                shutil.rmtree('./temp/')
                del data, out_image, d, row, col, nc_long_IMERG, T1, nc_lat_IMERG, no_data, out_transform, IMERG_temp_filename, destfile
                # The TRMM data grid information
                # Use the same dummy date defined above since TRMM has data up to present with less accurancy. The recomendation is to use IMERG data from 2014-03-12 and onward!
                # update my url with TRMM information
                myurl = url_TRMM_input + year + '/' + mon + '/'
                check2 = requests.get(myurl)
                if check2.status_code == 200:
                    filenames = check2._content
                    # getting one of the daily files at the monthly URL specified by DUMMY Date
                    filenames = pd.read_html(filenames)[0][1][3]
                    # Extract the TRMM nc4 files for the specific month
                    # trying here the first day since I am only interested on grid locations
                    # downloading one file
                    if not os.path.exists('./temp/'):
                        os.makedirs('./temp/')
                        destfile = './temp/' + filenames
                        filenames = myurl + filenames
                        r = requests.get(filenames, stream=True)
                        with open(destfile, 'wb') as fd:
                            fd.write(r.content)
                            fd.close()
                        # reading ncdf file
                        nc = netCDF4.Dataset(destfile, mode='r')
                        ###evaluate these values one time!
                        ###getting the y values (longitudes in degrees east)
                        nc_long_TRMM = nc.variables['lon'][:]
                        ####getting the x values (latitudes in degrees north)
                        nc_lat_TRMM = nc.variables['lat'][:]
                        ####getting the transform and resolutions for the IMERG raster data
                        xres_TRMM = (nc_long_TRMM[-1] - nc_long_TRMM[0]) / nc_long_TRMM.shape[0]
                        yres_TRMM = (nc_lat_TRMM[-1] - nc_lat_TRMM[0]) / nc_lat_TRMM.shape[0]
                        transform_TRMM = rasterio.transform.from_origin(west=nc_long_TRMM[0], north=nc_lat_TRMM[-1],
                                                                        xsize=xres_TRMM, ysize=yres_TRMM)
                        # extract data
                        data = nc.variables[myvarTRMM][:]
                        # reorder the rows
                        data = np.transpose(data)
                        # close the netcdf file link
                        nc.close()
                        # save the daily climate data values in a raster
                        TRMM_temp_filename = './temp/' + 'pcp_trmm_rough.tif'
                        TRMM = rasterio.open(TRMM_temp_filename, 'w', driver='GTiff', height=data.shape[0],
                                             width=data.shape[1], count=1, dtype=data.dtype.name, crs=polys.crs,
                                             transform=transform_TRMM)  #
                        TRMM.write(data, 1)
                        TRMM.close()
                        # extract the raster x,y values within the watershed (polygon)
                        with rasterio.open(TRMM_temp_filename) as src:
                            out_image, out_transform = rasterio.mask.mask(src, geoms, all_touched=True, crop=True)
                        # The out_image result is a Numpy masked array
                        # no data values of the TRMM raster
                        no_data = src.nodata
                        # extract the values of the masked array
                        data = out_image.data[0]
                        # extract the row, columns of the valid values
                        row, col = np.where(data != no_data)
                        src.close()
                        # Now I use How to I get the coordinates of a cell in a geotif? or Python affine transforms to transform between the pixel and projected coordinates with out_transform as the affine transform for the subset data
                        rc2xy = lambda r, c: (c, r) * T1
                        T1 = out_transform * rasterio.Affine.translation(0.5, 0.5)  # reference the pixel center
                        # Creation of a new resulting GeoDataFrame with the col, row and precipitation values
                        d = gpd.GeoDataFrame({'NAME': myvarTRMM, 'col': col, 'row': row}, crs=polys.crs)  #
                        # coordinate transformation
                        d['x'] = d.apply(lambda row: rc2xy(row.row, row.col)[0], axis=1)
                        d['y'] = d.apply(lambda row: rc2xy(row.row, row.col)[1], axis=1)
                        # geometry
                        d['geometry'] = d.apply(lambda row: shapely.geometry.Point(row['x'], row['y']), axis=1)
                        study_area_records_TRMM = gpd.sjoin(d, polys, how='inner', op='intersects')
                        study_area_records_TRMM = study_area_records_TRMM.reset_index()
                        study_area_records_TRMM = study_area_records_TRMM.rename(
                            columns={'index': 'TRMMiD', 'x': 'TRMMlONG', 'y': 'TRMMlAT'})
                        study_area_records_TRMM['NAME'] = study_area_records_TRMM['NAME'] + study_area_records_TRMM[
                            'TRMMiD'].astype(str)
                        # study_area_records_TRMM.to_csv('./TRMM_Table_result.txt',index=False)#
                        # study_area_records_TRMM[['TRMMiD','NAME','TRMMlONG','TRMMlAT','geometry']].to_file('./TRMM_Pcp_result.shp', driver='ESRI Shapefile',crs_wkt=polys_crs_wkt)#
                        shutil.rmtree('./temp/')
                        del data, out_image, d, row, col, T1, nc_long_TRMM, nc_lat_TRMM, no_data, out_transform, TRMM_temp_filename, destfile
                        # creating a similarity table that connects IMERG and TRMM grids
                        # calculate euclidean distances to know how to connect TRMM grids with IMERG grids
                        ee = pd.DataFrame(columns=study_area_records_TRMM.columns.values)
                        for i in range(study_area_records_IMERG.shape[0]):
                            study_area_records_TRMM['distVec'] = study_area_records_TRMM['geometry'].distance(
                                study_area_records_IMERG['geometry'][i])
                            ff = study_area_records_TRMM[
                                (study_area_records_TRMM.distVec <= study_area_records_TRMM.distVec.min())]
                            ee = ee.append(ff, ignore_index=True, sort=True)
                        ee = ee.rename(columns={'TRMMiD': 'CloseTRMMIndex', 'col': 'TRMMcol', 'row': 'TRMMrow'})
                        FinalTable = pd.DataFrame(
                            {'ID': study_area_records_IMERG['ID'], 'NAME': study_area_records_IMERG['NAME'],
                             'LONG': study_area_records_IMERG['LONG'], 'LAT': study_area_records_IMERG['LAT'],
                             'ELEVATION': study_area_records_IMERG['ELEVATION'], 'CloseTRMMIndex': ee['CloseTRMMIndex'],
                             'TRMMlONG': ee['TRMMlONG'], 'TRMMlAT': ee['TRMMlAT'], 'TRMMrow': ee['TRMMrow'],
                             'TRMMcol': ee['TRMMcol']})
                        # FinalTable.to_csv('./FinalTable.txt',index=False)#
                        #### Begin writing SWAT climate input tables
                        #### Get the SWAT file names and then put the first record date
                        if not os.path.exists(Dir):
                            os.makedirs(Dir)
                            for h in range(FinalTable.shape[0]):
                                filenameSWAT_TXT = Dir + FinalTable['NAME'][h] + '.txt'
                                # write the data begining date once!
                                swat = open(filenameSWAT_TXT, 'w')  #
                                swat.write(format(time_period[0], '%Y%m%d'))
                                swat.write('\n')
                                swat.close()
                            #### Write out the SWAT grid information master table
                            OutSWAT = pd.DataFrame(
                                {'ID': FinalTable['ID'], 'NAME': FinalTable['NAME'], 'LAT': FinalTable['LAT'],
                                 'LONG': FinalTable['LONG'], 'ELEVATION': FinalTable['ELEVATION']})
                            OutSWAT.to_csv(filenametableKEY, index=False)
                            #### Start doing the work!
                            #### iterate over days to extract record at IMERG grids estabished in 'FinalTable'
                            for kk in range(len(time_period)):
                                mon = time_period[kk].strftime('%m')
                                year = time_period[kk].strftime('%Y')
                                # Decide here whether to use TRMM or IMERG based on data availability
                                # Begin with TRMM first which means days before 2014-March-12
                                if time_period[kk].date() < datetime.date(2014, 3, 12):
                                    myurl = url_TRMM_input + year + '/' + mon + '/'
                                    check3 = requests.get(myurl)
                                    if check3.status_code == 200:
                                        filenames = check3._content
                                        # getting the daily files at each monthly URL
                                        filenames = pd.DataFrame({'Web File': pd.read_html(filenames)[0][1]})
                                        filenames = filenames.dropna()
                                        warnings.filterwarnings("ignore", 'This pattern has match groups')
                                        criteria = filenames['Web File'].str.contains('3B42.+(.nc4$)')
                                        filenames = filenames[criteria]
                                        filenames['Date'] = filenames['Web File'].str.extract('(\d\d\d\d\d\d\d\d)',
                                                                                              expand=True)
                                        filenames['Date'] = pd.to_datetime(filenames['Date'], format='%Y%m%d',
                                                                           errors='coerce')
                                        filenames = filenames[filenames['Date'] == time_period[kk]]
                                        if not os.path.exists('./temp/'):
                                            os.makedirs('./temp/')
                                        destfile = './temp/' + filenames['Web File'].values[0]
                                        filenames = myurl + filenames['Web File'].values[0]
                                        r = requests.get(filenames, stream=True)
                                        with open(destfile, 'wb') as fd:
                                            fd.write(r.content)
                                            fd.close()
                                            # reading ncdf file
                                            nc = xr.open_dataset(destfile)
                                            # looking only within the watershed
                                            nc = nc.merge(nc, geoms, join='inner')
                                            # evaluating precipitation at lat/lon points
                                            pcp_values = nc.interp(lon=FinalTable['TRMMlONG'],
                                                                   lat=FinalTable['TRMMlAT'], method='nearest')
                                            FinalTable['cell_values'] = pcp_values[myvarTRMM].data.diagonal()
                                            FinalTable['cell_values'] = FinalTable['cell_values'].fillna(-99.0)
                                            ### Looping through the IMERG points and writing out the daily climate data in SWAT format
                                            for h in range(FinalTable.shape[0]):
                                                filenameSWAT_TXT = Dir + FinalTable['NAME'][h] + '.txt'
                                                # write the data begining date once!
                                                with open(filenameSWAT_TXT, 'a') as swat:
                                                    np.savetxt(swat, [FinalTable['cell_values'].values[h]])
                                            shutil.rmtree('./temp/')
                                            ## Now for dates equal to or greater than 2014 March 12 (i.e., IMERG)
                                else:
                                    myurl = url_IMERG_input + year + '/' + mon + '/'
                                    check4 = requests.get(myurl)
                                    if check4.status_code == 200:
                                        filenames = check4._content
                                        # getting the daily files at each monthly URL
                                        filenames = pd.DataFrame({'Web File': pd.read_html(filenames)[0][1]})
                                        filenames = filenames.dropna()
                                        warnings.filterwarnings("ignore", 'This pattern has match groups')
                                        criteria = filenames['Web File'].str.contains('3B-DAY.+(.nc4$)')
                                        filenames = filenames[criteria]
                                        filenames['Date'] = filenames['Web File'].str.extract('(\d\d\d\d\d\d\d\d)',
                                                                                              expand=True)
                                        filenames['Date'] = pd.to_datetime(filenames['Date'], format='%Y%m%d',
                                                                           errors='coerce')
                                        filenames = filenames[filenames['Date'] == time_period[kk]]
                                        if not os.path.exists('./temp/'):
                                            os.makedirs('./temp/')
                                            destfile = './temp/' + filenames['Web File'].values[0]
                                            filenames = myurl + filenames['Web File'].values[0]
                                            r = requests.get(filenames, stream=True)
                                            with open(destfile, 'wb') as fd:
                                                fd.write(r.content)
                                                fd.close()
                                            # reading ncdf file
                                            nc = xr.open_dataset(destfile)
                                            # looking only within the watershed
                                            nc = nc.merge(nc, geoms, join='inner')
                                            # evaluating precipitation at lat/lon points
                                            pcp_values = nc.interp(lon=FinalTable['LONG'], lat=FinalTable['LAT'],
                                                                   method='nearest')
                                            FinalTable['cell_values'] = pcp_values[myvarIMERG].data.diagonal()
                                            FinalTable['cell_values'] = FinalTable['cell_values'].fillna(-99.0)
                                            ### Looping through the IMERG points and writing out the daily climate data in SWAT format
                                            for h in range(FinalTable.shape[0]):
                                                filenameSWAT_TXT = Dir + FinalTable['NAME'][h] + '.txt'
                                                # write the data begining date once!
                                                with open(filenameSWAT_TXT, 'a') as swat:
                                                    np.savetxt(swat, [FinalTable['cell_values'].values[h]])
                                            shutil.rmtree('./temp/')

    else:
        print ('Sorry' + ", " + start.strftime("%b") + "-" + start.strftime(
            '%Y') + ' is out of coverage for TRMM or IMERG data products.')
        print ('Please pick start date equal to or greater than 2000-Mar-01 to access TRMM and IMERG data products.')
        print ('Thank you!')


def send_email(to_email, unique_id):

    from_email = 'nasaaccess@gmail.com'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Your nasaaccess data is ready'

    msg['From'] = from_email
    msg['To'] = to_email

    #email content
    message = """\
        <html>
            <head></head>
            <body>
                <p>Hello,
                   <br>
                   Your nasaaccess data is ready for download at 
                   <a href="http://tethys-servir-mekong.adpc.net/apps/nasaaccess">
                        http://tethys-servir-mekong.adpc.net/apps/nasaaccess
                   </a>
                   <br>
                   Your unique access code is: <strong>""" + unique_id + """</strong><br>
                </p>
            </body>
        <html>
    """

    part1 = MIMEText(message, 'html')
    msg.attach(part1)

    gmail_user = 'nasaaccess@gmail.com'
    gmail_pwd = 'nasaaccess123'
    smtpserver = smtplib.SMTP('smtp.gmail.com', 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(gmail_user, gmail_pwd)
    smtpserver.sendmail(gmail_user, to_email, msg.as_string())
    smtpserver.close()