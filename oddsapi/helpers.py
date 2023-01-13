import datetime

def time_now():
    return datetime.datetime.now().replace(microsecond=0)
