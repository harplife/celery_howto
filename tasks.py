from worker import app, DatabaseTask
import secrets
import time
import sqlite3
from sqlite3 import Error
import requests


@app.task
def add(x, y):
    return x + y


@app.task
def mult(x, y):
    return x * y


@app.task
def subtract(x, y):
    result = str(x - y)
    print('now sleeping')
    for x in range(1,6):
        print(x)
        time.sleep(1)
    print('awake now')


@app.task(bind=True, name='test')
def test(self, n):
    print(f'Task {n} shall sleep now.')
    time.sleep(3)
    print(f'Task {n} is now awake!')


@app.task(base=DatabaseTask)
def db_call():
    print('db_call task is starting')
    try:
        c = db_call.db.cursor()
    except:
        print('db_call connection failed')
    else:
        print('db_call connection cursor is created')
    finally:
        c.execute(f'SELECT 210 + 210;')
        print('db_call select is executed')


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


@app.task(bind=True, name='web_test')
def web_test(self, n):
    print(f'Task {n} shall make a request now.')
    r = requests.get('http://localhost:8080')
    if r.status_code == 200:
        print(f'Task {n} API request succeeded!')
    else:
        print(f'Task {n} API request FAILED.')
