import os
import platform
from celery import Celery
from celery.schedules import crontab

from datetime import timedelta


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_api.settings")

app = Celery("library_api")

if platform.system() == "Windows":
    app.conf.worker_pool = "solo"

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.result_backend = "redis://localhost:6379/0"

app.autodiscover_tasks()

# Celery beat schedule (for periodic tasks)
# app.conf.beat_schedule = {
#     "check-overdue-borrowings-every-30-seconds": {
#         "task": "borrowings.tasks.check_overdue_borrowings",
#         "schedule": timedelta(seconds=30),
#     },
# }

from celery.schedules import crontab


app.autodiscover_tasks()
app.conf.result_backend = "redis://localhost:6379/0"

app.conf.beat_schedule = {
    "test_celery": {
        "task": "borrowings.test_celery",
        # 'schedule': crontab(minute='0', hour='*/1'),
        "schedule": crontab(minute="*/1"),
        "args": (),
    },
}

app.conf.timezone = "UTC"
