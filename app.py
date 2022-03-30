import os
import logging
from flask import Flask
from celery import Celery
#from apps import json_page
from dotenv import load_dotenv
import apps

load_dotenv()

log = logging.getLogger(f'{__name__}')
logging.basicConfig(filename='app.log', level=logging.INFO)


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL','redis://localhost:6379/0')
app.config['result_backend'] = os.getenv('CELERY_RESULT_BACKEND','redis://localhost:6379/0')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], include=['apps.json_page'])
celery.conf.update(app.config)

@celery.task()
def add_together(a, b):
    return a + b

#app.title = 'Writing the Records of Valhalla'
#env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
#app.config.from_object(env_config)

#app.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))
