"""
exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os
import time
import traceback
import signal
import sys

from django.core.wsgi import get_wsgi_application
from dotenv import dotenv_values

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
# adjust the Python version in the line below as needed
sys.path.append(
    dotenv_values(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, ".env")
    )["PYTHON_SITE_PACKAGES_PATH"]
)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "expendituresTracer.production_settings"
)

try:
    application = get_wsgi_application()
except Exception:
    # Error loading applications
    if "mod_wsgi" in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)
