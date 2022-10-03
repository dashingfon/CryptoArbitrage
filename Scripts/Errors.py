'''Errors module containing all the errors definition'''


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
