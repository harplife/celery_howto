from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
import secrets
import time
import sqlite3
from sqlite3 import Error
import requests


app = Celery('tasks', broker='amqp://rabbit_dev')

db_conn = None


@worker_process_init.connect
def init_worker(**kwargs):
    global db_conn
    print('initializing database connection for worker.')
    try:
        db_conn = sqlite3.connect('sqlite.db')
    except Error as e:
        db_conn = None
        print(e)


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global db_conn
    if db_conn:
        print('closing database conection for worker.')
        db_conn.close()
    else:
        print('there is no data connection to close.')
