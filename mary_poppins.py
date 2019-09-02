import json
import re
import requests
from lxml import html
import datetime
import time
import random
from flask import Flask, redirect, url_for
import threading
import subprocess
import google_tts

#
# # Transit Info
#
# Description: Interfaces w/ the BART API to find information for a specified
# station, and gets the next northbound and soundbound trains.
#
# Results: Converts the API output into an object with the following type:
#
#   type Train = { 'destination' :: Destination,
#                  'departure_time' :: Time,
#                }
#   type DepartureInfo = { 'northbound' :: [Train], 'southbound' :: [Train] }
#
# The set of such objects is constrained so that at most two trains going to
# the same destination will ever be listed. There will also be at most 5 trains
# listed in each direction.


class BART_API:

    def __init__(self, api_key, station):
        self.api_key = api_key
        self.station = station
        self.request_url = 'http://api.bart.gov/api/etd.aspx?cmd=etd&orig=%s&key=%s&json=y' % (
            station, api_key)

    def get_next_trains(self):
        r = requests.get(self.request_url)

        if 200 != r.status_code:
            return None

        try:
            info = json.loads(r.text)
        except json.decoder.JSONDecodeError:
            print(r.text)
            return None

        if 'root' not in info or \
           'station' not in info['root'] or \
           len(info['root']['station']) == 0 or \
           'etd' not in info['root']['station'][0]:

            return None

        departure_info = {
            'North': {},
            'South': {},
        }

        destinations = info['root']['station'][0]['etd']

        for destination in destinations:
            dest = destination['destination']
            for train in destination['estimate']:
                dir = train['direction']
                if dest not in departure_info[dir]:
                    departure_info[dir][dest] = []

                if train['minutes'] != 'Leaving':
                    departure_info[dir][dest] += [int(train['minutes'])]

        for dir in departure_info:
            for dest in departure_info[dir]:
                departure_info[dir][dest].sort()
                departure_info[dir][dest] = departure_info[dir][dest][0:2]
            departure_info[dir] = \
                sorted([(dest, time) for dest in departure_info[dir]
                        for time in departure_info[dir][dest]],
                       key=lambda p: p[1])[0:5]

        return departure_info


class TwitterAPI:

    def get_last_tweet(self):
        url = 'https://twitter.com/QueeriousLabs'

        r = requests.get(url)
        if r.status_code != 200:
            return None

        try:
            root = html.fromstring(r.text)

            tweet_link = sorted([(el, url) for el, kind, url, _ in root.iterlinks()
                                 if kind == 'href' and '/QueeriousLabs/status' in url], key=lambda link: link[1])[-1][0]

            tweet_content = str(tweet_link.getparent().getparent(
            ).getparent()[1].text_content()).strip()

            # tweet_links = sorted([link for link in root.xpath('//a') if 'href' in link.attrs and '/QueeriousLabs/status' in link.attrs['href']], key=lambda link: link.attrs['href'])[-1]

            return tweet_content
        except:
            return None


def bart_info():

    bart_api = BART_API('MW9S-E7SL-26DU-VV8V', 'civc')
    departure_info = bart_api.get_next_trains()

    if departure_info is None:
        sentences = ['There are currently no BART trains running...']
    else:
        sentences = ['Upcoming BART times...']
        for dir in departure_info:
            sentences += ['The next %sbound trains are...' % dir]
            seen = False
            for departure in departure_info[dir]:
                sentences += ['%s train in %i %s...' % (
                    re.sub('[^a-zA-Z]', ' ', departure[0]), departure[1], 'minute' if departure[1] == 1 else 'minutes')]

    return sentences


def tweet_info():

    twitter_api = TwitterAPI()

    last_tweet = re.sub('(ftp://|http://|https://)\S+|…',
                        ' ', twitter_api.get_last_tweet())

    return ['I last tweeted...',
            last_tweet]


def intro():

    dt = datetime.datetime.now()

    return ['Thank you for hacking at Queerious Labs...',
            dt.strftime(
                'The time now is %I:%M %p on %A %B %-d, %Y...'),
            ]


def should_repeat_time(xs):
    return len(xs) > 3


def outro(repeat):

    if repeat:
        dt = datetime.datetime.now()
        sentences = [dt.strftime(
            'The time now is %I:%M %p on %A %B %-d, %Y...')]
    else:
        sentences = []

    sentences += ['Hack the planet, and remember to donate to Queerious Labs...']

    return sentences


def random_quote():

    quotes = ['Never send a boy to do a woman\'s job.',
              'Remember... hacking is more than just a crime... it\'s a survival trait.',
              'Never fear, I is here.',
              ['FYI man, alright. You could sit at home, and do like...',  'absolutely nothing, and your name goes through like 17 computers a day...',
                  '1984? Yeah right, man. That\'s a typo. Orwell is here now. He\'s livin\' large.', 'We have no names, man. No names. We are nameless!',
                  'Can I score a fry?'],
              ]

    return random.choice(quotes)


def get_volume():
    if 0 == subprocess.call('which amixer', shell=True):
        amixer_output = subprocess.check_output(
            'amixer sget PCM,0', shell=True).decode('utf-8')
        m = re.search('\[(\d+)%\]', amixer_output)
        if m:
            return int(m.group(1))
        else:
            return 75
    else:
        return 75


def set_volume(vol):
    if 0 == subprocess.call('which amixer', shell=True):
        subprocess.call('amixer set PCM,0 ' + str(vol) + '%', shell=True)


def with_temporary_volume(vol, callback):
    old = get_volume()
    set_volume(vol)
    callback()
    set_volume(old)


class MaryPoppins:

    def __init__(self):
        self.mute_time = None
        self.talk_thread = None
        self.last_said = []
        self.volume = 90

    def unmute(self):
        self.mute_time = None
        print('Mary is now unmuted.')

    def mute(self):
        self.mute_time = datetime.datetime.now()
        print('Mary is now muted until ' + str(self.mute_time))

    def set_volume(self, vol):
        self.volume = max(70, vol)

    def clear_old_mute_time(self):
        if self.mute_time is not None and \
                (datetime.datetime.now() - self.mute_time).seconds > 3600:
            self.unmute()

    def should_speak(self):
        self.clear_old_mute_time()
        return self.mute_time is None

    def main(self):

        print('Main Mary Poppins loop running...')

        try:
            while True:

                if True:  # datetime.datetime.now().minute in [0, 30]:
                    if not self.should_speak():
                        print('Currently muted.')
                    else:

                        sentences = []

                        sentences += intro()

                        sentences += bart_info()

                        sentences += tweet_info()

                        sentences += outro(should_repeat_time(sentences))

                        quote = random_quote()

                        self.last_said = sentences + \
                            [' '.join(quote)
                             if isinstance(quote, list)
                             else quote]

                        print()
                        print(16 * '=')
                        print()
                        print('\n'.join(sentences))
                        print()
                        print(' '.join(quote) if isinstance(
                            quote, list) else quote)

                        with_temporary_volume(
                            mary.volume,
                            lambda:
                            google_tts.say_with_permission(
                                'en', sentences, lambda: self.should_speak()))

                        time.sleep(1)

                        with_temporary_volume(
                            mary.volume,
                            lambda:
                            google_tts.say_with_permission(
                                'en',
                                quote if isinstance(
                                    quote, list) else [quote],
                                lambda: self.should_speak()))

                time.sleep(5)
        except KeyboardInterrupt:
            pass


mary = MaryPoppins()

t = threading.Thread(target=mary.main)
t.start()

app = Flask(__name__)


@app.route('/')
def mary_status():
    global mary

    if mary.mute_time is None:
        mute_status = '<span style="color: #00CC00;">unmuted</span>'
        mute_action = 'mute'
    else:
        mute_finish = mary.mute_time + datetime.timedelta(seconds=3600)
        mute_status = '<span style="color: red;">muted</span> until %i:%i' % \
            (mute_finish.hour % 12, mute_finish.minute)
        mute_action = 'unmute'

    page = '''
<html>
  <head>
    <meta http-equiv="refresh" content="30;URL='/'" />
  </head>
  <body>
    <h1>Mary Poppins is currently %s.</h1>
    <h2>All mutes take effect at the end of the current line Mary Poppins is saying.</h2>
    <h1><a href="/%s">Click here to %s Mary Poppins.</a></h1>
    <hr/>
    <h3>Set Volume</h3>
    <p>The current play volume is %i</p>
    <p>
        <a href="/vol/70">70%%</a>&nbsp;&nbsp;&nbsp;&nbsp;
        <a href="/vol/75">75%%</a>&nbsp;&nbsp;&nbsp;&nbsp;
        <a href="/vol/80">80%%</a>&nbsp;&nbsp;&nbsp;&nbsp;
        <a href="/vol/85">85%%</a>&nbsp;&nbsp;&nbsp;&nbsp;
        <a href="/vol/90">90%%</a>&nbsp;&nbsp;&nbsp;&nbsp;
        <a href="/vol/95">95%%</a>
    </p>
    <hr/>
    <h3>Most recent info:</h3>
    <p>%s</p>
  </body>
</html>''' % (mute_status, mute_action, mute_action, mary.volume, '<br/>'.join(mary.last_said))

    return page


@app.route('/mute')
def mute_mary():
    global mary
    mary.mute()
    return redirect(url_for('mary_status'))


@app.route('/unmute')
def unmute_mary():
    global mary
    mary.unmute()
    return redirect(url_for('mary_status'))


@app.route('/vol/<vol>')
def set_volumne(vol):
    global mary
    mary.set_volume(int(vol))
    return redirect(url_for('mary_status'))


app.run(host='0.0.0.0', port=5000)
