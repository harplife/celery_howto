# Celery 활용 가이드

Task Queue/Background Task하면 대표적인 파이썬 패키지인 Celery를 사용하는 가이드.
(우분투 20.04 :: 파이썬 3.8 :: Celery 4.4.7)

Advanced Level 코딩, 또는 웹 개발에 근접할 수록 자주 접하는 것;
Multi-processing, Concurrency, Parallel Processing, Multi-Threading 등이 있다.

파이썬 자체에서도 multi-processing, asyncio 등의 native 패키지가 있긴 있는데,
복잡하기도 하고 기능들도 제한적이여서 위에 것들 사용해보려면 아주 아주 마니 마니 귀찮다.
특히나 Background Task, Queue/Pooling, Task Status 등의 필.수.기.능.들을 직접 구현해서 만드려면
그냥 차라리 하바드 가는게 낳을 것이다.

그래서 나~~개발전직저렙캐~~를 위해 만들어진게 Celery라는 아주 건강에 좋은 패키지가 있다.

Celery가 해주는 것은 다음과 같다;

1. 여러 Task를 관리할 수 있는 Celery Worker Task 서버가 운영이 된다.
2. 내가 만든 function을 `@app.task`만 위에 얹으면 task로 변환이 된다.
3. celery가 알아서 task를 multi-processing 또는 multi-thread로 처리해준다.
4. task에 대한 status도 제공해준다.
5. flower라는 task 모니터닝 웹서버와 쉽게 연동된다.
6. `--pool` 옵션으로 process 사용, 또는 thread 사용을 정할 수 있다.
7. Broker(예: Redis, RabbitMQ)를 지정해주면 지가 알아서 Task Queue를 만든다.
8. Backend(예: Redis, MySQL)를 지정해주면 지가 알아서 Task Result를 유지한다.
9. 도커 컨테이너에 할당된 CPU 자원을 넘지 않으며, thread를 사용할 경우 Celery가 알아서 조정한다.
10. Gevent, 또는 Eventlet을 쉽게 연동해서 사용할 수가 있다 <-- 이 들은 thread이긴 한데 좀 더 똑똑한 thread다.

# 목차

1. 간단한 용어 정리
2. 인스톨
3. 실행
4. 라우팅
5. Primitive 업무 요청

# 간단한 용어 정리

- __Task__: 처리할 업무.
  - __Signature__: 업무의 내역을 호출하며, 여러 업무를 묶어주는 역할을 한다.
  - __Primitive__: 서로 관계성을 가진 여러 업무를 처리하는 방식 (예: group, chain, chord, 등).
- __Worker__: 업무 담당자. Celery 서버라고도 볼 수 있다.
  - __Mingle__: 여러 worker가 같이 일할 수 있다. 보통 1 machine == 1 worker 지만, 경우에 따라 1 machine에 여러 worker를 두어 업무 효율을 높일 수가 있다고 한다. 또는, 업무의 유형에 따라 worker를 지정할 수가 있다.
- __Queue__: 업무 요청 리스트. Worker는 지정된 Queue로부터 Task들을 가져온다.
- __Broker__: Queue 담당자. 필수 요소이며, RabbitMQ가 제일 대표적인 예시다.
- __Backend__: 업무 결과 리스트 담당자. 업무 결과는 주로 DB에 저장되기 때문에 꼭 결과물을 return 할 필요가 없다. 따라서, backend는 필수 요소가 아니다. 하지만 Chain, Group 등의 기능들을 사용하려면 잠시만이라도 결과값이 유지되어야 하기 때문에 Redis, Memcache 등의 memory 기반 저장소가 사용된다. Backend로 Redis가 많이 사용된다.

# 인스톨

Celery를 제대로 사용하기 위해선 Broker가 될 RabbitMQ와,
Result Backend가 될 Redis도 설치해야 되기 때문에,
이 가이드에선 Celery, RabbitMQ, Redis 각각 도커 컨테이너로 분리해서 사용하는 방안을 제시한다.

1) 네트워크 생성 - `docker network create celery_net`

- Celery가 RabbitMQ와 Redis에 쉽게 통신할 수 있도록 네트워크를 만들어 주는게 좋다.

2) 파이썬 컨테이너 생성

- `docker run -it --net celery_net -p 5555:5555 --name celery_py -v celery_vol:/root/celery ubuntu:python zsh`
- 저자는 Ubuntu 환경에 파이썬 설치된 이미지가 있어서 그걸 사용하는데, `python:alpine`을 사용해도 문제는 없을 것이다.
- 필요 패키지 설치
  - `pip install celery flower gevent redis requests flask`

3) RabbitMQ 컨테이너 생성

- `docker run -v rabbitmq_data:/var/lib/rabbitmq -d --hostname my_rabbit --name rabbit_dev --net celery_net rabbitmq`

4) Redis 컨테이너 생성

- `docker run -v redis_data:/data --name redis_dev --net celery_net -d redis redis-server --appendonly yes`

# 사용방법(Simple)

파이썬 컨테이너, RabbitMQ 컨테이너, Redis 컨테이너 모두 돌아가고 있는 상태여야 한다.

## Celery Worker 실행

Celery 사용하는 방법은 Flask와 많이 유사하다.

Flask에 main과 route이 있다면,
Celery에서는 worker와 tasks가 있다.

밑에 코드는 덧셈 task 하나를 갖춘 celery worker의 코드이다.

```python
# worker.py
from celery import Celery

app = Celery(__name__)
app.conf.update(
    {
        'broker_url': 'amqp://rabbit_dev',
        'result_backend': 'redis://redis_dev',
        'imports': ('tasks')  # tasks.py에 명시된 task들을 가져온다.
    }
)
```

```python
# tasks.py
from worker import app

@app.task
def add(x, y):
    return x+y
```

Celery worker 실행은

1. 터미널에 `celery worker --app=worker.app --loglevel=INFO` 명령으로 실행할 수 있으며,
2. 또는 파이썬 파일 내에서 `__name__=='__main__'` 방식으로도 실행이 가능하다.

Celery 설정은

1. 터미널 command에서 가능하지만, 파일 내애서도 설정이 가능하다. \[[관련 문서](https://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#configuration)\]
2. 기본 설정으론 celery는 multi-processing으로 구현되며, 프로세스 개수는 CPU core 수대로 자동으로 맞춘다.
3. 실행 명령어에 `--pool=gevent`를 추가하면 multi-threading으로 구현된다.
4. 실행 명령어에 `--concurrency=숫자`를 추가하면 Celery가 사용할 process/thread 개수를 숫자만큼 정할 수 있다.
   참고로, I/O task 분량이 많은 경우 thread가 제일 적절하며, CPU 활용량이 높은 task들은 process가 적절하다.

## Task 요청

Celery Worker에 Task를 요청하는 방식은 아주 간단하다.

일단 worker를 실행해주고, 밑에 코드를 실행해본다.

```python
# test.py
from tasks import add

def make_request(n):
    # Task를 여러번 한꺼번에 요청한다.
    for _ in range(n):
        # 등록한 Task 중 add(덧셈 함수)를 사용한다.
        add.apply_async(args=[116, 124])  # Task args: x값, y값

make_request(10)
```

Celery worker 측에서 로그가 찍히는 것을 확인하면, 10개의 Task 요청 로그와 Task 완료 로그가 보인다.

## 결과값 호출

Backend가 정상적으로 설정이 되어있다면, `apply_async()`로 task 요청한 상태값을 받아올 수가 있다.
이러한 상태값을 `AsyncResult`라고 부르는데, 이 상태값으로서 task의 상태를 확인할 수 있으며,
task가 완료된 경우 이의 결과값을 받을 수가 있다.

예시 코드:

```python
>>> result = add.apply_async(args=[210, 210])  # Task 상태값
>>> if result.ready() == True:  # Task 처리가 완료된 경우,
        result.get()  # Task 결과값을 불러온다
420
```

__~참고~__

Celery 공식 문서에서는 결과값을 받지 않도록 권장을 한다.
그 이유는 결과값을 받으려면 결국 Task가 끝날때까지 기다려야 한다는 뜻인데,
이는 celery를 사용하는 목적인 __비동기 처리__와 상이되기 대문이다.

그렇다고 무조건 backend가 필요 없는 것은 아니다.
좀 더 복잡한 Task 처리방식, Primitive 기능을 사용하기 위해선 backend가 필요하다.
이 부분에 대해선 [공식 문서](https://docs.celeryproject.org/en/latest/userguide/canvas.html#important-notes)를 참고할 것.

# 라우팅(Intermediate)

Task에는 밑에와 같이 여러 유형이 있을 수 있다.

- 오래 걸리는 task
- 짧게 걸리는 task
- 계산이 많은 task
- 계산이 적은 task
- API 호출 위주의 task
- 최우선순위의 task

하나의 worker로는 다양한 task를 처리 할 수 없다.
각 task가 요구하는 구조/리소스를 갖춘 worker가 필요하다.
따라서, 각 task에 queue가 지정될 수 있으며,
각 queue를 담당하는 worker를 지정할 수가 있다.

예를 들어, 최우선순위의 task, `urgent_call`이라는 task가 있으면,
이 task를 `high_priority`라는 queue로 지정하고,
이 queue만 담당하는 worker가 따로 실행된다.
이로서 `urgent_call` task만 이 worker가 처리하기 때문에,
다른 task들로 인하여 연기될 염려가 없다.

위와 같은 케이스를 코드로 구현하면 다음과 같다.

## Celery Worker 실행

사용방법(Simple) - Celery Worker 실행 부분에서는 Celery Worker와 Task들이 하나의 파일로 코딩되어 있었지만, 라우팅을 적용하기 위해선 Celery Worker 부분과 Task 부분을 각각의 파일로 분리한다.

Celery Worker 코드, 정확히는 Celery Worker 설정에서 라우팅을 설정한다.
일반적인 task, `normal_call`은 `low_priority` queue로 라우팅 된다.
최우선순위 task, `urgent_call`은 `high_priority` queue로 라우팅 된다.

```python
# worker.py
from celery import Celery

app = Celery(__name__)
app.conf.update(
    {
        'broker_url': 'amqp://rabbit_dev',
        'result_backend': 'redis://redis_dev',
        'imports': ('tasks'),  # tasks.py에 명시된 task들을 가져온다.
        'task_routes': {
            'normal_call': {'queue': 'low_priority'},
            'urgent_call': {'queue': 'high_priority'}
        }
    }
)
```

Task를 정의하는 파일에선 task의 이름을 꼭 지정해줘야 한다.

```python
# tasks.py
from worker import app

@app.task(name='normal_call')
def norm_msg():
    print('Hello, World.')

@app.task(name='urgent_call')
def emrg_msg():
    print('The world is in danger!')
```

Worker는 2개 실행해주면 되는데, 여기서 `--queues`를 지정해주는게 중요하다.
Worker를 여러 개 실행하려 하면 pid가 겹친다고 에러가 뜨는데,
이를 해결하기 위해 `--hostname`을 지정해서 각 worker에 이름을 부여한다.

1. `normal_call`을 담당할 worker:
   `celery worker --app=worker.app --hostname=worker.low_priority@%h --queues=low_priority`
2. `urgent_call`을 담당할 worker:
   `celery worker --app=worker.app --hostname=worker.high_priority@%h --queues=high_priority`

## Task 요청

두 개의 worker가 실행되고 있으면 밑에와 같이 테스트를 진행하면 된다.

```python
from tasks import norm_msg, emrg_msg

def make_request(n):
    for _ in range(n):
        norm_msg.apply_async()
        emrg_msg.apply_async()

make_request(10)
```

로그를 확인해보면 `urgent_call` task들이 `normal_call`에 밀리지 않고
거의 동시에 실행되는 것을 확인할 수가 있다.

만약에 위 처럼 Task가 두 가지로 분류된 것이 아니고, 한 개의 Task를 상황에 따라 다른 Queue로 보내야 하는 경우,
`apply_async(queue='urgent_call')`처럼 라우팅이 가능하다.

## Dynamic 라우팅

[참고](https://www.distributedpython.com/2018/06/05/dynamic-task-routing/)

# 캔버스(Advanced)

Celery 공식 문서에서 task 정의, task 처리, task 연결 등의 전체적인 디자인을 Canvas(캔버스)라고 한다. [링크](https://docs.celeryproject.org/en/latest/userguide/canvas.html)

Canvas의 중요 요소는 Signature와 Primitive가 있다.

Task의 정보를 Signature라고 부르며,
Task를 처리하는 방식을 Primitive라고 한다.

## Signature

Signature는 자기의 존재를 뜻하는데,
프로그래밍 위주로 이해를 하자면 signature는 task의 wrapper이다.

덧셈을 하는 Task 위주로 생각해보자.

`2 + 2`를 하는 task를 실행하지 않고 일단 정보만 가지고 싶다.
그런데 `r = add(2, 2)`를 코딩하면 현재 프로세스에서 task가 실행되버린다.
`r = add.apply_async(args=[2,2])`를 하면 worker로 task가 보내져 실행되버린다.
이 문제는 `s = add.signature(args=[2,2])`로 간단히 해결된다.

Task의 정보를 굳이 유지할 필요가 있을까~ 싶으면 당연히 답은 있고,
그건 바로 Partial과 Callback이라는 것이다.

참고로, signature는 간단히 s로도 대체가 된다.
`add.signature() == add.s()`

### Partial

Partial은 '부분적'이라는 뜻을 함유한다.
Signature에 들어갈 argument가 일부분만 들어가면 이를 partial이라 부른다.

뺄셈을 하는 Task 위주로 생각해보자.

뺄샘(`x - y`)을 하기 위해서 task에 x, y 값을 넣어줘야 한다.
y값을 먼저 받았기에, `partial = subtract.signature(args=[y])`를 먼저 생성해준다.
나중에 x값을 받아 `partial.apply_async(args=[x])`를 실행하면 곧바로 task 요청이 나간다.

여기서 주의할 점은, `apply_async`로 추가되는 argument 값은 `signature`에 지정되었던 값의 앞으로 추가된다.

### Callback

Callback은 '다시 불러온다'라는 뜻이 있다.
Celery에서는 task와 task를 연결해주는 작업을 Callback이라 한다.
이 기능은 `apply_async` 함수에서 `link`라는 argument로 사용된다.

덧셈과 곱셈을 하는 2개의 task 위주로 생각해본다.

풀어야 하는 수식, `(x + y) * z`이 있다.
이 수식을 풀기 위해선 먼저 `* z`를 partial signature로 정의해야 한다.
`partial = mult.signature(args=[z])`
이 다음에는 덧셈 task를 만드는 동시에 `link=partial`로 콜백을 넣어준다.
`add.apply_async(args=[x, y], link=partial)`
위와 같이 한다면, `x + y`가 먼저 계산되고, 그 결과값과 `z`값의 곱셈이 계산된다.

여기도 주의할 점은, `x + y` 결과값이 `z` 값의 앞으로 간다는 점이다.

## Primitive

Primitive의 뜻은 근원, 근본, 또는 원시적인~ 이다.
Celery에서는 task를 처리하는 방식을 primitive라고 하는데,
사실 저자에게 와닫지 않는 정의다.

Task를 처리하는 방식에는 총 6가지가 있다.

- Chain
- Chunks
- Group
- Chord
- Map
- Starmap

자주 반복하며 말하지만, Primitive를 사용하려면 무조건 backend가 필요하다.

### Chain

Task에 Task에 Task를 줄줄히 연결하는 작업을 Chain이라고 한다.
첫 Task를 제외하고는 나머지 Task는 모두 partial signature이며,
순서대로 모두 callback이 된다.

예시 코드:

```python
>>> from celery import chain
>>> # 2 + 2 + 4 + 8
>>> res = chain(add.s(2, 2), add.s(4), add.s(8))()
>>> res.get()
16
>>> # pipe로도 구현된다
>>> res = (add.s(2, 2) | add.s(4) | add.s(8))()
>>> res.get()
16
```

### Chunks

Data Processing에 아주 용이하게 쓰일 듯한 기능이다.
리스트에 있는 값들을 지정된 interval에 따라 여러 task로 나누어 처리하는 방식이다.
리턴된 chain의 결과값은 각 task의 결과값을 포함한 리스트이며,
각 task의 결과값에는 interval 범위 내에 있던 값에 처리된 결과값이다.

예시 코드:

```python
>>> items = zip(range(10), range(10))  # [(0,0), (1,1), ..]
>>> res = add.chunks(items, 5).apply_async()  # 10개의 값을 5개의 task로 분리
>>> res.get()  # 각 task에 2개의 결과값이 있다
[[0,2], [4,6], [8,10], ..]
```

### Group

Group(그룹)은 리스트에 담긴 모든 task를 한꺼번에 처리해준다.
다른 한마디로 말하자면, Parallel Processing이다.

예시 코드:

```python
>>> from celery import group
>>> res = group(add.s(i, i) for i in range(10))()
>>> res.get(timeout=1)
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
```

### Chord

그룹과 유사하다. 그룹에 Callback 하나가 추가된 것 뿐이다.

예시 코드:

```python
# tasks.py에 xsum 함수 추가; 여러 값을 다 더하는 함수다.
@app.task
def xsum(numbers)
    return sum(numbers)
```

```python
>>> from celery import chord
>>> res = chord((add.s(i, i) for i in range(10)), xsum.s()).apply_async()
>>> res.get()
90
```

### Map & Starmap

Map과 Starmap은 Group하고 비슷한데,
Group은 리스트에 있는 Task들을 동시에(parallel) 처리하는 방식이며,
Map/Starmap은 리스트에 있는 값들을 __하나의 Task로__ 순서대로(sequential) 처리하는 방식이다.

Map과 Starmap의 차이점은 들어가는 argument의 개수다.

Map 예시 코드:

```python
>>> args = [1, 2, 3]
>>> square.map(args)
[square(x) for x in [1, 2, 3]]
>>> res = square.map(args).apply_async()
>>> res.get()
[1, 4, 9]
```

Starmap 예시 코드:

```python
>>> args = zip(range(3), range(3))
>>> add.starmap(args)
[add(*x) for x in [(0,0), (1,1), (2,2)]]
>>> res = add.starmap(args).apply_async()
>>> res.get()
[0, 2, 4]
```

## Immutable

Immutable, 즉, '불변성'이란 뜻인데 Signature의 옵션으로 들어가는 boolean 값이다.
보통 Chain/Chord에 속한 signature의 결과값은 다음 task의 결과값으로 변경이 되는데,
immutable 설정이 되어 있는 경우 이전 값이 유지가 된다.

보통 signature는 `task.s()`로 간단히 부르듯이,
immutable은 `task.si()`로 간단히 부를 수 있다.
`add.signature(immutable=True) == add.si()`

예시 코드 (Chain):

```python
>>> res = (add.si(2,2) | add.si(4,4) | add.si(8,8)).apply_async()
>>> res.get()  # chain의 가장 뒷 계산값이 나온다. 
16
>>> res.parent.get()
8
>>> res.parent.parent.get()
4
```

예시 코드 (Chord):

```python
>>> # 유저들에게 경고 메시지를 보낸 후 관리자에게 알림.
>>> chord(
...    (send_alert.s(u) for u in users),
...    notify_admin.si()
...    ).apply_async(),
```

# DB 컨넥션 설정

이 부분은 좀 더 검토해볼 필요가 있다는 점을 먼저 표기한다.
이유는, 이 섹션이 미완성일 뿐만이 아니라,
DB 컨넥션 한 개로서 DB 관련된 모든 Task를 처리할지,
Task 한개씩 처리할 때마다 DB 컨넥션을 만들어야 할지,
Stackoverflow 조차도 이 점을 제대로 답변해주지 못 하기 때문이다.

심지어, Celery에서 multi-processing 사용할 때 와, multi-threading을 사용할 때와 상황이 다르니..

일단 참고할 만한 내용은 여기에 정리하되,
직접 테스트 해보지 않는 이상 그 무엇이 더 낳은 방법이라 할 수가 없다.

## Worker 프로세스 시작 전 DB 컨넥션 설정

이 설정은 Multi-processing을 사용할 경우에만 적용된다.

Celery에서 이 용도로 사용하라고 아주 간편한 기능을 제공해준다.

- `worker_process_init` : 초기에 worker process가 시작될 시 실행되는 부분.
  Task가 시작되기 전이 아닌, worker가 시작되며 process들이 준비가 될 때를 말한다.
- `worker_process_shutdown` : worker process가 종료될 시 실행되는 부분
  Task가 종료될 때가 아닌, worker가 종료되며 process들도 종료될 때를 말한다.

예시 코드:

```python
# worker.py
from celery.signals import worker_process_init, worker_process_shutdown
import sqlite3
from sqlite3 import Error

db_conn = None

@worker_process_init.connect
def init_worker(**kwargs):
    global db_conn
    try:
        db_conn = sqlite3.connect('sqlite.db')
    except Error as e:
        db_conn = None

@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global db_conn
    if db_conn:
        db_conn.close()
```

`celery worker --app=worker.app --loglevel=INFO --concurrency=10`로 worker를 실행하면,
로그에 10개의 프로세스가 각각 DB 컨넥션을 생성했다는 것을 확인할 수가 있다.

## Task 시작 전 DB 컨넥션 설정

이 설정은 딱히 프로세스/쓰레드 구분이 필요없으며, 정의된 task마다 DB 컨넥션을 지정할 수 있다.
[참고](https://docs.celeryproject.org/en/latest/userguide/tasks.html#instantiation)

문제점은 이런 방식으로 했을 때 DB 컨넥션을 닫는 방법을 아직 모른다는 것..

예시 코드:

```python
# worker.py
# 밑에 코드 추가
from celery import Task
import sqlite3

class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = sqlite3.connect('sqlite.db')
            print('DB 연결이 되었습니다.')
        return self._db
```

```python
# tasks.py
from worker import DatabaseTask

@app.task(base=DatabaseTask)
def db_call():
    c = db_call.db.cursor()
    c.execute('SELECT 210 + 210;')
```

`celery worker --app=worker.app --loglevel=INFO --pool=gevent --concurrency=1000`로 worker를 실행하고,
`group(db_call.s() for x in range(10))()`로 task 요청을 보내면 첫 번째 task에 `DB 연결이 되었습니다`라고 로그가 찍히는게 보이고,
그 후로 나머지 task에는 따로 DB 연결을 하는 작업이 실행되지 않는 것을 확인할 수가 있다.

# 참고사항

TODO
1. Flower 연동
2. DB 연결 (worker 초기 설정) 방안 
