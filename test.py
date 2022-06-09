
graph = {}
graph['a'] = ['b','c']
graph['b'] = ['d','e']
graph['e'] = ['f','g','a']
graph['f'] = ['h','i']
graph['c'] = ['j','a','b']
graph['j'] = ['k','a']
graph['k'] = ['l','m']


def dive(graph,depth, limit, node,goal,path):
    result = []
    if depth <= limit and node in graph:
        for i in graph[node]:
            if i == goal:
                result.append(path + [i])
            elif depth < limit:
                result += dive(graph,depth + 1,limit,i,goal,path + [i]) 

    return result         

def depthLimitedSearch(graph,limit,goal):
    result = []
    path = [goal]
    depth = 1
    if goal in graph:
        start = graph[goal]
    else:
        start = []

    for i in start:
        result += dive(graph,depth + 1,limit,i,goal,path + [i])
        
    return result


#ans = depthLimitedSearch(graph,3,'a')
#print(f'The answer is: {ans}')

from functools import wraps
class limiter():
    def __init__(self, amount, period):
        self.amount = amount
        self.period = period

    def __call__(self, func):
        @wraps(func)
        def wrapper():
            originalResult = func()
            # needs editing
            modifiedResult = originalResult.upper()
            return modifiedResult
        return wrapper
limit = limiter(2,4)

@limit
def reef():
    return 'yeah'

print(reef())