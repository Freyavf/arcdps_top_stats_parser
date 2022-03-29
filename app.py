#import os
import logging
from flask import Flask
#from apps import json_page

#load_dotenv()

log = logging.getLogger(f'{__name__}')
logging.basicConfig(filename='app.log', level=logging.INFO)

app = Flask(__name__)

#app.title = 'Writing the Records of Valhalla'
#env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
#app.config.from_object(env_config)

#app.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))
