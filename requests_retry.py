import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def get(*args, **kwargs):
    for i in range(3):
        try:
            return requests.get(*args, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print("Down")

    return None
