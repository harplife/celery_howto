from flask import Flask
import time
from tasks import db_call
from celery import group

app = Flask(__name__)


@app.route('/')
def home():
    return {'hello': 'world'}


@app.route('/db_call_test/<int:numero>')
def db_call_test(numero):
    res = group([db_call.si() for x in range(numero)], ignore_result=True).apply_async()
    res.forget()
    return f'{numero} db_call task request sent.'


@app.route('/db_call_iter/<int:numero>')
def db_call_iter(numero):
    for x in range(numero):
        db_call.delay()
    return f'{numero} db_call task request sent.'


@app.route('/fake_call_test/<int:numero>')
def fake_call_test(numero):
    for x in range(numero):
        pass
    return 'fake call completed.'


if __name__ == '__main__':
    app.run(debug=True, port=5555, host='0.0.0.0')
