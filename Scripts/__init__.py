import logging
import logging.config
import pathlib

path: pathlib.PurePath = pathlib.PurePath(__file__).parent.parent
logging.config.fileConfig(str(path.joinpath("logging.conf")))
CONFIG_PATH: str = 'scripts\\Config.json'
