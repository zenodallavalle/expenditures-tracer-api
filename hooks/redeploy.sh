#!/bin/sh

cd /var/www/vhosts/expenditures-tracer-api/
git pull -f origin master
. env/bin/activate
rm -rf static/
python manage.py collectstatic
python manage.py migrate
deactivate
sudo service apache2 restart