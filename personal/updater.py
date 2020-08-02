from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import personal.views

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(personal.views.updateProducts, 'interval', minutes=120)
    scheduler.start()