#!/bin/sh

ssh-keyscan github.com >> ~/.ssh/known_hosts
cd /var/www/vhosts/expenditures-tracer-api/
git pull -f origin master
. env/bin/activate
rm -rf static/
python manage.py collectstatic --settings "expendituresTracer.production_settings"
python manage.py migrate --settings "expendituresTracer.production_settings"
deactivate
sudo service apache2 restart