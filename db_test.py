from tasks import db_test


def do_things():
    for x in range(1,11):
        db_test.delay(x)


if __name__ == '__main__':
    print('just about to do things')
    do_things()
    for x in range(1,11):
        print(x)
    print('done things')
