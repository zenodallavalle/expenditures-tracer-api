from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from expendituresTracer.celery import app
from logging import getLogger
import os
import re


logger = getLogger(__name__)

DT_FORMAT = "%Y-%m-%d-%H-%M-%S"


def build_filename():
    now = timezone.now()
    return f"dump_production_{now.strftime(DT_FORMAT)}.json"


def get_backup_datetime_from_filename(filename):
    match = re.search(r".*(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}).*", filename)
    if match:
        return timezone.datetime.strptime(match.group(1), DT_FORMAT)
    return None


def get_backup_files(path):
    files_and_dts = []
    for filename in os.listdir(path):
        dt = get_backup_datetime_from_filename(filename)
        if dt:
            files_and_dts.append((filename, dt))
    files_and_dts.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in files_and_dts]


@app.task(name="dump_database_data")
def dump_database_data(path):  # pragma: no cover
    call_command(
        "dumpdata",
        "main",
        "auth.user",
        output=(dest_path := os.path.join(path, build_filename())),
        indent=2,
    )
    logger.info(f"Database dump created at {dest_path}")
    if getattr(settings, "MAX_DUMP_FILES", None) is not None:
        backup_files = get_backup_files(path)
        for file in backup_files[settings.MAX_DUMP_FILES :]:
            os.remove(os.path.join(path, file))
            logger.info(f"Removed old database dump: {file}")
    return str(dest_path)
