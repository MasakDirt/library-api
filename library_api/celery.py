import os
import platform

from celery import Celery
from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_api.settings")

app = Celery("library_api")

if platform.system() == "Windows":
    app.conf.worker_pool = "solo"

app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.result_backend = (
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
)

app.autodiscover_tasks()

app.conf.timezone = "UTC"
