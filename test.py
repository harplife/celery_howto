from tasks import test


def do_things():
    for x in range(1,11):
        test.delay(x)


if __name__ == '__main__':
    print('just about to do things')
    do_things()
    for x in range(1,11):
        print(x)
    print('done things')
