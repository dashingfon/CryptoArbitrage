import logging


def preplogger(name: str,
               file: str,
               formatt: str = '%(levelname)s:%(name)s:%(asctime)s:%(message)s',
               fileLevel: int = logging.INFO,
               streamLevel: int = logging.DEBUG):
    '''
    function to prepare the logger object
    '''
    formatter = logging.Formatter(formatt)

    file_handler = logging.FileHandler(file)
    file_handler.setLevel(fileLevel)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(streamLevel)
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
