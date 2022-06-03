# coding=utf-8
import json
import string
from typing import Any

import log


def get_config() -> dict[str, Any]:
    log.info("reading config file...")
    with open("config.json", mode="r") as file:
        return json.load(file)


def clean_hashtag(hashtag: str) -> str:
    return "".join(x for x in hashtag if x in string.digits + string.ascii_letters)
