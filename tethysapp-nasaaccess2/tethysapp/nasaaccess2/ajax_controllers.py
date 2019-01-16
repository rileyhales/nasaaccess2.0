import os, datetime, logging
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.core.files import File
from .forms import UploadShpForm, UploadDEMForm
from .config import *
from .model import *
from .app import nasaaccess2
import pprint

logging.basicConfig(filename=nasaaccess_log, level=logging.INFO)


def run_nasaaccess(request):
    """
    Controller to call nasaaccess R functions.
    """
    # Get selected parameters and pass them into nasaccess R scripts

    print("Starting the NasaAccess Ajax Script")

    try:
        start = request.POST.get('startDate')
        start = str(datetime.datetime.strptime(start, '%b %d, %Y').strftime('%Y-%m-%d'))
        print("start date:", start)
        end = request.POST.get(str('endDate'))
        end = str(datetime.datetime.strptime(end, '%b %d, %Y').strftime('%Y-%m-%d'))
        print("end date:", end)
        functions = request.POST.getlist('functions[]')
        print('fuctions', functions)
        watershed = request.POST.get('watershed')
        print('watershed', watershed)
        dem = request.POST.get('dem')
        print('dem', dem)
        email = request.POST.get('email')
        print('email', email)
        user_workspace = os.path.join(nasaaccess2.get_user_workspace(request.user).path)
        print('user workspace', user_workspace)
        os.chmod(user_workspace, 0o777)

        # identify where each of the input files are located in the server
        shp_path_sys = os.path.join(data_path, 'workspaces/app_workspace/shapefiles', watershed, watershed + '.shp')
        shp_path_user = os.path.join(user_workspace, 'shapefiles', watershed, watershed + '.shp')
        shp_path = ''
        if os.path.isfile(shp_path_sys):
            shp_path = shp_path_sys
        elif os.path.isfile(shp_path_user):
            shp_path = shp_path_user
        print('shape path:', shp_path)

        dem_path_sys = os.path.join(data_path, 'workspaces/app_workspace/DEMfiles', dem, dem + '.tif')
        dem_path_user = os.path.join(user_workspace, 'DEMfiles', dem + '.tif')
        dem_path = ''
        if os.path.isfile(dem_path_sys):
            dem_path = dem_path_sys
        elif os.path.isfile(shp_path_user):
            dem_path = dem_path_user
        print('dem path:', dem_path)

        # create a new folder to store the user's requested data
        unique_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        unique_path = os.path.join(data_path, 'workspaces/app_workspace/outputs', unique_id)
        print('unique path', unique_path)

        # create a temporary directory to store all intermediate data while nasaaccess functions run
        tempdir = os.path.join(data_path, 'temp', 'workspaces/app_workspace/temp/earthdata', unique_id)
        print('tempdir', tempdir)

        # functions = ','.join(functions)
        logging.info(
            "Trying to run {0} functions for {1} watershed from {2} until {3}".format(functions, watershed, start, end))

        args = (unique_path, shp_path, dem_path, start, end, email, unique_id, tempdir, functions)
        print('these are the args that are going to be passed to the functions')
        pprint.pprint(args)

        print('the time has come, starting a new thread to run your processes')
        threading.Thread(target=nasaaccess_controller, args=args, name='SWAT Backend Thread').start()
        # result = nasaaccess_controller(args)
        return JsonResponse({'Result': 'nasaaccess is running'})
    except Exception as e:
        return JsonResponse({'Error': str(e)})


def upload_shapefiles(request):
    """
    Controller to upload new shapefiles to app server and publish to geoserver
    """

    if request.method == 'POST':
        form = UploadShpForm(request.POST, request.FILES)
        id = request.FILES['shapefile'].name.split('.')[0]      # Get name of the watershed from the shapefile name
        if form.is_valid():
            form.save()  # Save the shapefile to the nasaaccess data file path
            perm_file_path = os.path.join(data_path, 'shapefiles', id)
            user_workspace = os.path.join(nasaaccess2.get_user_workspace(request.user).path, 'shapefiles')
            shp_path_user = os.path.join(user_workspace, id)
            if os.path.isfile(perm_file_path) or os.path.isfile(shp_path_user):
                logging.info('file already exists')
            else:
                logging.info('saving shapefile to server')
                if not os.path.exists(user_workspace):
                    os.makedirs(user_workspace)
                    os.chmod(user_workspace, 0o777)
                    os.makedirs(shp_path_user)
                    os.chmod(shp_path_user, 0o777)
                if not os.path.exists(shp_path_user):
                    os.makedirs(shp_path_user)
                    os.chmod(shp_path_user, 0o777)
                upload_shapefile(id, shp_path_user)  # Run upload_shapefile function to upload file to the geoserver
            return HttpResponseRedirect('../')  # Return to Home page
    else:
        return HttpResponseRedirect('../')  # Return to Home page


def upload_tiffiles(request):
    """
    Controller to upload new DEM files
    """
    if request.method == 'POST':
        form = UploadDEMForm(request.POST, request.FILES)
        id = request.FILES['DEMfile'].name
        if form.is_valid():
            form.save(commit=True)
            perm_file_path = os.path.join(data_path, 'DEMfiles', id)
            dem_path_user = os.path.join(nasaaccess2.get_user_workspace(request.user).path, 'DEMfiles')
            if os.path.isfile(perm_file_path) or os.path.isfile(dem_path_user):
                logging.info('file already exists')
            else:
                logging.info('saving dem to server')
                if not os.path.exists(dem_path_user):
                    os.makedirs(dem_path_user)
                    os.chmod(dem_path_user, 0o777)
                upload_dem(id, dem_path_user)
            return HttpResponseRedirect('../')
    else:
        return HttpResponseRedirect('../')


def download_data(request):
    """
    Controller to download data using a unique access code emailed to the user when their data is ready
    """
    if request.method == 'POST':
        # get access code from form
        access_code = request.POST['access_code']

        # identify user's file path on the server
        unique_path = os.path.join(data_path, 'outputs', access_code, 'nasaaccess_data')

        # compress the entire directory into a .zip file
        def zipfolder(foldername, target_dir):
            zipobj = zipfile.ZipFile(foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
            rootlen = len(target_dir) + 1
            for base, dirs, files in os.walk(target_dir):
                for file in files:
                    fn = os.path.join(base, file)
                    zipobj.write(fn, fn[rootlen:])

        zipfolder(unique_path, unique_path)

        # open the zip file
        path_to_file = os.path.join(data_path, 'outputs', access_code, 'nasaaccess_data.zip')
        f = open(path_to_file, 'r')
        myfile = File(f)

        # download the zip file using the browser's download dialogue box
        response = HttpResponse(myfile, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=nasaaccess_data.zip'
        return response
