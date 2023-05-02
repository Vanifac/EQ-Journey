tags = {
        'purple': '[95m',
        'blue': '[94m',
        'cyan': '[96m',
        'green': '[92m',
        'yellow': '[93m',
        'red': '[91m',
        'white': '[0m'
}


def orful(text, color='white'):
    print(f'\033{tags.get(color, "")}{text}\033[0m')


def red(text):
    orful(text, 'red')


def green(text):
    orful(text, 'green')
