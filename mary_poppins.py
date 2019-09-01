import json
import re
import requests
from lxml import html
import datetime
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


def main():
    bart_api = BART_API('MW9S-E7SL-26DU-VV8V', 'civc')

    departure_info = bart_api.get_next_trains()

    sentences = []

    dt = datetime.datetime.now()
    sentences += ['Thank you for hacking at Queerious Labs...',
                  dt.strftime('The time now is %I:%M %p on %A %B %-d, %Y...'),
                  'Upcoming BART times...',
                  ]

    for dir in departure_info:
        sentences += ['The next %sbound trains are...' % dir]
        seen = False
        for departure in departure_info[dir]:
            sentences += ['%s train in %i %s...' % (
                re.sub('[^a-zA-Z]', ' ', departure[0]), departure[1], 'minute' if departure[1] == 1 else 'minutes')]

    twitter_api = TwitterAPI()

    last_tweet = re.sub('(ftp://|http://|https://)\S+|…',
                        ' ', twitter_api.get_last_tweet())

    sentences += ['I last tweeted...',
                  last_tweet,
                  dt.strftime('The time now is %I:%M %p on %A %B %-d, %Y...'),
                  'Be excellent to each other, hack the planet, and remember to donate to Queerious Labs...']

    print()
    print('\n'.join(sentences))

    google_tts.say('en', sentences)


main()
