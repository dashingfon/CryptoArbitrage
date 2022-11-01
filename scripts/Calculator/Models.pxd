cdef class Token:
    cdef readonly str name
    cdef readonly str address
    cdef readonly str address_lower


cdef class Via:
    cdef readonly str name
    cdef readonly str pair
    cdef readonly int fee
    cdef readonly str router


cdef class Swap:
    cdef readonly Token fro
    cdef readonly Token to
    cdef readonly Via via


cdef class Route:
    cdef public list swaps
    cdef public float UsdValue
    cdef public int EP
    cdef public list rates
    cdef public int capital


cdef class Spliter:
    cdef public list items
    cdef public int start
    cdef public int end
