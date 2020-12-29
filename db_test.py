from tasks import db_test
import time


def do_things():
    for x in range(1,11):
        db_test.delay(x)


if __name__ == '__main__':
    i = 0
    in_operation = True
    while in_operation:
        if i > 10:
            in_operation = False
        i += 1
        print('just about to do things')
        do_things()
        for x in range(1,11):
            print(x)
        print('done things')
        time.sleep(3)
