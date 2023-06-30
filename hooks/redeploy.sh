#!/bin/sh

cd /var/www/vhosts/expenditures-tracer-api/
git pull -f origin master
. env/bin/activate

python manage.py migrate --settings "expendituresTracer.production_settings"
python manage.py collectstatic --no-input --settings "expendituresTracer.production_settings"

deactivate
sudo service apache2 restart