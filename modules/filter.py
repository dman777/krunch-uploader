import logging

class MyFilter(object):
    """Filters for log messages. We want to keep info and error messages seperated"""

    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level

