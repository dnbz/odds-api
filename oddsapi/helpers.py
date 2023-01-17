import datetime
import logging


def time_now():
    return datetime.datetime.now().replace(microsecond=0)


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO
    )
