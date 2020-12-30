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


@app.task
def add(x, y):
    result = str(x + y)
    print(f'added result: {result}')


@app.task
def subtract(x, y):
    result = str(x - y)
    print('now sleeping')
    for x in range(1,6):
        print(x)
        time.sleep(1)
    print('awake now')


@app.task
def test(n):
    print(f'Task {n} shall sleep now.')
    time.sleep(3)
    print(f'Task {n} is now awake!')


@app.task
def db_add(x, y):
    global db_conn
    if db_conn:
        c = db_conn.cursor()
        c.execute(f'SELECT {x} + {y};')
        print('the db has answered:' + str(c.fetchone()[0]))
    else:
        print('no database connection was found.')


@app.task
def db_subtract(x, y):
    global db_conn
    if db_conn:
        c = db_conn.cursor()
        c.execute(f'SELECT {x} - {y};')
        print('the db has answered:' + str(c.fetchone()[0]))
    else:
        print('no datbase connection was found.')


@app.task
def db_test(n):
    print(f'Task {n} shall ask DB now.')
    global db_conn
    if db_conn:
        c = db_conn.cursor()
        c.execute(f'SELECT 421 - 1;')
        print(f'the db has answered to Task {n}:' + str(c.fetchone()[0]))
    else:
        print('no datbase connection was found.')


@app.task
def web_test(n):
    print(f'Task {n} shall make a request now.')
    r = requests.get('http://localhost:8080')
    if r.status_code == 200:
        print(f'Task {n} API request succeeded!')
    else:
        print(f'Task {n} API request FAILED.')
