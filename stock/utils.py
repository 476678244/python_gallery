from datetime import datetime

TIME_FORMAT = "%m-%d-%Y %H"


def strptime(time_expr):
    return datetime.strptime(time_expr, TIME_FORMAT)
