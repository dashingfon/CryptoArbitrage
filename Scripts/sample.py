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
from operator import eq


def main():
    print('Hello World')

def equal(list1,list2):
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]

    return False if list_dif else True

r = [{'e':4},{'r':2}]
e = [{'r':2},{'e':4}]
print(equal(r,e))
