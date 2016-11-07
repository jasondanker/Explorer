from flask import Flask

myapp = Flask(__name__)
myapp.config.from_object('config')

from app import views, models