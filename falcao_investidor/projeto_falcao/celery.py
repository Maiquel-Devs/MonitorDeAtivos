# projeto_falcao/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projeto_falcao.settings')
app = Celery('projeto_falcao')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()