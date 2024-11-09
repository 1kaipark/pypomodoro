
def log(msg: str, fpath: str = 'log.txt') -> None:
    from datetime import datetime as dt
    """writes to a log.txt file"""
    with open(fpath, 'a+') as h:
        h.write('[' + str(dt.now()) + '] ' + msg + '\n')