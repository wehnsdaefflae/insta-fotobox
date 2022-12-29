# coding=utf-8
import json
import string
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

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


def frame_image(image: Image.Image, frame: Image.Image, window_coordinates: tuple[int, int, int, int]) -> Image.Image:
    image_width, image_height = image.size
    aspect_ratio_image = image_width / image_height
    window_width = window_coordinates[2] - window_coordinates[0]
    window_height = window_coordinates[3] - window_coordinates[1]
    aspect_ratio_window = window_width / window_height

    if aspect_ratio_window < aspect_ratio_image:
        print("window is too narrow, scaling according to height")
        factor = image_height / window_height
    else:
        print("window is too wide, scaling according to width")
        factor = image_width / window_width

    framed_image = frame.resize((int(frame.size[0] * factor), int(frame.size[1] * factor)))
    resized_window_width = int(window_width * factor)
    resized_window_height = int(window_height * factor)
    print(f"resized window: {resized_window_width:.0f} x {resized_window_height:.0f}")

    image_position = (
        int(window_coordinates[0] * factor + max(0., (resized_window_width - image_width) / 2)),
        int(window_coordinates[1] * factor + max(0., (resized_window_height - image_height) / 2))
    )
    print(f"image position in frame: {image_position[0]:.0f}, {image_position[1]:.0f}")

    print(f"image size: {image.size}, "
          f"frame size: {frame.size}, "
          f"resized frame size: {framed_image.size}, "
          f"window size: {window_width:d}x{window_height:d}, "
          f"resized window size: {resized_window_width:.0f}x{resized_window_height:.0f}, "
          f"image position: {image_position}")
    cropped_image = image.crop((0, 0, resized_window_width, resized_window_height))
    alpha_channel_frame = ImageOps.invert(framed_image.split()[3])
    mask_box = (
        int(window_coordinates[0] * factor),
        int(window_coordinates[1] * factor),
        int(window_coordinates[0] * factor + resized_window_width),
        int(window_coordinates[1] * factor + resized_window_height)
    )
    framed_image.paste(cropped_image, box=image_position, mask=alpha_channel_frame.crop(mask_box))
    # framed_image.paste(cropped_image, box=image_position)
    return framed_image


if __name__ == "__main__":
    framed = frame_image(
        Image.open("images/6210769181387243502.jpg"),
        Image.open("resources/gold-picture-frame-1 - rotate.png"),
        (147, 137, 1527, 1083))
    framed.show()
