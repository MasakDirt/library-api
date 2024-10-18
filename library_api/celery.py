import os
import platform
from celery import Celery

from datetime import timedelta


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_api.settings")

app = Celery("library_api")

if platform.system() == "Windows":
    app.conf.worker_pool = "solo"

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.result_backend = "redis://localhost:6379"

app.autodiscover_tasks()

app.autodiscover_tasks()
app.conf.result_backend = "redis://localhost:6379"

app.conf.beat_schedule = {
    "test_celery": {
        "task": "borrowings.tasks.check_overdue_borrowings",
        "schedule": timedelta(seconds=30),
        "args": (),
    },
}

app.conf.timezone = "UTC"
