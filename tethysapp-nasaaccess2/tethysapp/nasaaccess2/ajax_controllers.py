import os, datetime, zipfile
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.core.files import File
from .forms import UploadShpForm, UploadDEMForm
from .config import data_path
from .model import *


def run_nasaaccess(request):

    """
    Controller to call nasaaccess R functions.
    """
    # Get selected parameters and pass them into nasaccess R scripts
    try:
        start = request.POST.get('startDate')
        d_start = str(datetime.datetime.strptime(start, '%b %d, %Y').strftime('%Y-%m-%d'))
        end = request.POST.get(str('endDate'))
        d_end = str(datetime.datetime.strptime(end, '%b %d, %Y').strftime('%Y-%m-%d'))
        functions = request.POST.getlist('functions[]')
        watershed = request.POST.get('watershed')
        dem = request.POST.get('dem')
        email = request.POST.get('email')
        result = nasaaccess_run(email, functions, watershed, dem, d_start, d_end)
        return JsonResponse({'Result': str(result)})
    except Exception as e:
        return JsonResponse({'Error': str(e)})

def upload_shapefiles(request):

    """
    Controller to upload new shapefiles to app server and publish to geoserver
    """

    if request.method == 'POST':
        form = UploadShpForm(request.POST, request.FILES)
        id = request.FILES['shapefile'].name.split('.')[0] # Get name of the watershed from the shapefile name
        perm_file_path = os.path.join(data_path, 'shapefiles')
        if form.is_valid():
            if os.path.isfile(perm_file_path):
                print('file already exists')
                upload_shapefile(id)
            else:
                print('saving shapefile to server')
                form.save() # Save the shapefile to the nasaaccess data file path
                upload_shapefile(id) # Run upload_shapefile function to upload file to the geoserver
            return HttpResponseRedirect('../') # Return to Home page
    else:
        return HttpResponseRedirect('../') # Return to Home page


def upload_tiffiles(request):
    """
    Controller to upload new DEM files
    """
    if request.method == 'POST':
        form = UploadDEMForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('../')
    else:
        return HttpResponseRedirect('../')


def download_data(request):
    """
    Controller to download data using a unique access code emailed to the user when their data is ready
    """
    if request.method == 'POST':
        #get access code from form
        access_code = request.POST['access_code']

        #identify user's file path on the server
        unique_path = os.path.join(data_path, 'outputs', access_code, 'nasaaccess_data')

        #compress the entire directory into a .zip file
        def zipfolder(foldername, target_dir):
            zipobj = zipfile.ZipFile(foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
            rootlen = len(target_dir) + 1
            for base, dirs, files in os.walk(target_dir):
                for file in files:
                    fn = os.path.join(base, file)
                    zipobj.write(fn, fn[rootlen:])

        zipfolder(unique_path, unique_path)

        #open the zip file
        path_to_file = os.path.join(data_path, 'outputs', access_code, 'nasaaccess_data.zip')
        f = open(path_to_file, 'r')
        myfile = File(f)

        #download the zip file using the browser's download dialogue box
        response = HttpResponse(myfile, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=nasaaccess_data.zip'
        return response