'''module containing all the custom errors definitions'''


class BlockchainNotSetup(Exception):
    pass


class NoBlockchainContract(Exception):
    pass


class incorrectInput(Exception):
    pass


class InvalidSession(Exception):
    pass


class InvalidMode(Exception):
    pass


class InvalidBlockchainObject(Exception):
    pass


class CannotInitializeDirectly(Exception):
    pass


class PrivateKeyNotSet(Exception):
    pass


class EmptyBlockchainUrl(Exception):
    pass


class UnequalRouteAndRouters(Exception):
    pass
