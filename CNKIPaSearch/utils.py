from datetime import datetime


def date2str(date=None, year=None):
    if date is None:
        date = datetime(year=year, month=1, day=1)
    date_string = date.strftime('%Y-%m-%d')
    return date_string


def str2date(text):
    date = datetime.strptime(text, '%Y-%m-%d')
    return date
