import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chips_server.settings')

app = Celery('chips_server', broker='redis://localhost:6379')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
