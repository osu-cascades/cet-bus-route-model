from flask import Flask
import threading
import time
from log import log

app = Flask(__name__)

@app.route('/')
def buses():
  return {}

def log_task():
  log()

t = threading.Thread(target=log_task)
t.start()
