'''from functools import wraps
import time
import dotenv
'''

#  Ratelimit module Usage

"""
from ratelimit import limits, RateLimitException, sleep_and_retry

AMOUNT = 1
PERIOD = 1

@sleep_and_retry
@limits(calls = AMOUNT, period = PERIOD)
def test(self):
    print('testing...')

"""

'''
import os
curr = os.path.dirname(__file__)
parent = os.path.split(curr)[0]
file = os.path.join(parent, 'Data', 'Aurora', 'arbRoute.json')
print(file)
'''
import requests
from bs4 import BeautifulSoup

#SOURCE = 'https://arbiscan.io/address/'
SOURCE = 'https://aurorascan.dev/address/'

def get(address):
    url = SOURCE + address
    response = requests.request('GET',url)
    print(response.status_code)
    return response.text

def extract(content):
    price = {}
    soup = BeautifulSoup(content, 'html.parser')
    tokensList = soup.find_all('li',class_ = 'list-custom')
    for token in tokensList:
        raw = token.find(class_ = 'list-amount').string
        rawPrice = str(raw).split()
        price[rawPrice[1]] = float(rawPrice[0].replace(',',''))

    return price

#price = extract(get('0x03B666f3488a7992b2385B12dF7f35156d7b29cD'))
#print(price)
