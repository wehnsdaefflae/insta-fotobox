# coding=utf-8
import json
import string
from pathlib import Path
from typing import Any

import requests

import log


def get_config(path: str) -> dict[str, Any]:
    log.info("reading config file...")
    with open(path, mode="r") as file:
        return json.load(file)


def save_image_from_url(filename: Path, image_url: str):
    image = requests.get(image_url)
    with filename.open(mode="wb") as file:
        file.write(image.content)


def clean_hashtag(hashtag: str) -> str:
    return "".join(x for x in hashtag if x in string.digits + string.ascii_letters)
