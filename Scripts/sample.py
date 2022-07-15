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
import time

def r(value):
    counter = 1
    for i in range(value):
        yield f'yielding the value {value} {counter}/{value} times '
        counter += 1

def reep(values):
    for i in values:
        for j in r(i):
            yield j

print(time.ctime())
