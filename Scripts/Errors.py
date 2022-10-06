'''Module containing all the Errors definition'''


class InvalidTokensArgument(Exception):
    pass


class InvalidExchangesArgument(Exception):
    pass


class IncompletePrice(Exception):
    pass


class ErrorExtractingPrice(Exception):
    pass


class InvalidBlockchainObject(Exception):
    pass


class PollingRuntimeError(Exception):
    pass
