import logging


class _IncludeLoggerMeta(type):
    def __init__(cls, what, bases=None, _dict=None):
        super().__init__(what, bases, _dict)
        setattr(cls, "logger", logging.getLogger(f"{cls.__module__}.{cls.__name__}"))


class LoggerMixin(metaclass=_IncludeLoggerMeta):
    logger: logging.Logger
