import requests
import urllib.parse
import random
import string
import os
import re
from subprocess import call
import requests_retry


def say(vol, lang, lines, download_done=None):

    say_with_permission(
        vol, lang, lines,
        should_continue=lambda: True,
        download_done=download_done)


def say_with_permission(vol, lang, lines, should_continue, download_done=None):

    say_sequence = []

    for line in lines:
        url = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=%s&client=tw-ob&q=%s' % (
            lang, line[0:200])
        output = 'files/' + ''.join(random.choice(string.hexdigits)
                                    for i in range(32)) + '.mp3'
        r = requests_retry.get(url)

        if r and 200 == r.status_code:
            if not os.path.isdir('files'):
                os.makedirs('files')
            with open(output, 'wb') as f:
                f.write(r.content)
            say_sequence += [output]

    if download_done:
        download_done()

    try:
        for file in say_sequence:
            print('Saying ' + file)
            if not should_continue():
                break
            else:
                call('mpg123 %s 2>/dev/null' % file, shell=True)
        for file in say_sequence:
            os.remove(file)

    except KeyboardInterrupt:
        for file in say_sequence:
            os.remove(file)

        raise KeyboardInterrupt
