# !python
# cython: profile=True


cdef calculate(dict cache, Route route):
    pass

def findAllProspects(dict cache, list routes) -> list[Route]:
    cdef Route r
    cdef float UsdValue
    cdef long EP
    cdef long index
    cdef long capital

    for r in routes:
        pass

def findProspect(dict cache, list routes) -> tuple[Route, int]:
    cdef Route r
