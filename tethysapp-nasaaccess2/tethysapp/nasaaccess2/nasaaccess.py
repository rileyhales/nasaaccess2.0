from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, sys, os, time


email = sys.argv[1]
functions = sys.argv[2].split(',')
unique_id = sys.argv[3]
shp_path = sys.argv[4]
dem_path = sys.argv[5]
unique_path = sys.argv[6]
tempdir = sys.argv[7]
start = sys.argv[8]
end = sys.argv[9]

os.chdir(tempdir)

time.sleep(120)

for func in functions:
    print(func)
    if func == 'GPMpolyCentroid':
        output_path = unique_path + '/GPMpolyCentroid/'
        os.makedirs(output_path, 0777)
        print('running GPMpoly')
        # GPMpolyCentroid(output_path, shp_path, dem_path, start, end)
    elif func == 'GPMswat':
        output_path = unique_path + '/GPMswat/'
        os.makedirs(output_path, 0777)
        print('running GPMswat')
        # GPMswat(output_path, shp_path, dem_path, start, end)
    elif func == 'GLDASpolyCentroid':
        output_path = unique_path + '/GLDASpolyCentroid/'
        os.makedirs(output_path, 0777)
        print('running GLDASpoly')
        # GLDASpolyCentroid(tempdir, output_path, shp_path, dem_path, start, end)
    elif func == 'GLDASwat':
        output_path = unique_path + '/GLDASwat/'
        os.makedirs(output_path, 0777)
        print('running GLDASwat')
        # GLDASwat(output_path, shp_path, dem_path, start, end)

from_email = 'nasaaccess@gmail.com'
to_email = 'spencermcdonald11@gmail.com'

msg = MIMEMultipart('alternative')
msg['Subject'] = 'Your nasaaccess data is ready'

msg['From'] = from_email
msg['To'] = to_email

message = """\
    <html>
        <head></head>
        <body>
            <p>Hello,<br>
               Your nasaaccess data is ready for download at <a href="http://tethys-servir-mekong.adpc.net/apps/nasaaccess">http://tethys-servir-mekong.adpc.net/apps/nasaaccess</a><br>
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