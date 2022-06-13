from functools import wraps
import time
import dotenv

# definition

def RateLimited(maxPerSecond):
    mininterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def ratelimitedFunction(*args,**kwargs):
            elapsed = time.process_time_ns() - lastTimeCalled[0]
            lefttowait = mininterval - elapsed
            if lefttowait > 0:
                print('waiting...')
                time.sleep(lefttowait)
            ret = func(*args, **kwargs)
            lastTimeCalled[0] = time.process_time_ns()
            return ret
        return ratelimitedFunction
    return decorate

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

class test():
    def __init__(self):
        pass
    
    @RateLimited(10)
    def test(self):
        print('testing...')


test = test()
for i in range(20):
    test.test()


#print(reef())

"""
arbitrage to do list

1. find out working with 
* .env
* time
* infura
* retelimit

2. setup infura account

2. install web3 and other dependencies

2. poll routes

3. create addresses

4. start writing controller



"""