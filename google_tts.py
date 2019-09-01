import requests
import urllib.parse
import random
import string
import os
import re
from subprocess import call


def say(lang, lines):

    say_sequence = []

    for line in lines:
        url = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=%s&client=tw-ob&q=%s' % (
            lang, line[0:200])
        output = 'files/' + ''.join(random.choice(string.hexdigits)
                                    for i in range(32)) + '.mp3'
        r = requests.get(url)

        if 200 == r.status_code:
            if not os.path.isdir('files'):
                os.makedirs('files')
            with open(output, 'wb') as f:
                f.write(r.content)
            say_sequence += [output]

    try:
        for file in say_sequence:
            call('mpg123 %s 2>/dev/null' % file, shell=True)
    except:
        for file in say_sequence:
            os.remove(file)
