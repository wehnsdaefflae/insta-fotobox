# coding=utf-8
import sys
import pathlib
import logging

_logger = logging.getLogger(name="root")
_logger.setLevel(logging.DEBUG)

file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler = logging.FileHandler(f"{pathlib.Path(sys.argv[0]).stem:s}.log")
file_handler.setFormatter(file_format)
file_handler.setLevel(logging.DEBUG)
_logger.addHandler(file_handler)

out_format = logging.Formatter("%(message)s")
out_handler = logging.StreamHandler(sys.stdout)
out_handler.setFormatter(out_format)
out_handler.setLevel(logging.INFO)
_logger.addHandler(out_handler)


def debug(*args, **kwargs):
    _logger.debug(*args, **kwargs)


def info(*args, **kwargs):
    _logger.info(*args, **kwargs)


def warning(*args, **kwargs):
    _logger.warning(*args, **kwargs)


def error(*args, **kwargs):
    _logger.error(*args, **kwargs)


def critical(*args, **kwargs):
    _logger.critical(*args, **kwargs)


def fatal(*args, **kwargs):
    _logger.fatal(*args, **kwargs)
