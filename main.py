# coding=utf-8
import json
import random
import string

import time
from pathlib import Path
from typing import Any

import requests
from requests import Response

import log


class ImageBot:
    def __init__(self):
        self.hashtag = ""
        self.scrapfly_key = None

        self.started_at = round(time.time())
        # self.started_at = -2

        self.processed = set()

        self.image_dir = Path("images/")
        self.image_dir.mkdir(exist_ok=True)

        self.post_limit = -1

        log.info("initializing...")

    def _print_photo(self, image_url: str):
        image = requests.get(image_url)

        file_name = f"{self.hashtag:s}-{round(time.time()):d}.jpg"
        with open(self.image_dir / file_name, mode="wb") as file:
            file.write(image.content)

    def _get_page(self, hashtag: str) -> Response:
        if self.scrapfly_key is not None:
            url = f"https://api.scrapfly.io/scrape?key={self.scrapfly_key:s}&url=https%3A%2F%2Fwww.instagram.com%2Fexplore%2Ftags%2F{self.hashtag:s}%2F%3F__a%3D1&tags=project%3Adefault&proxy_pool=public_residential_pool&asp=true"
        else:
            url = f"https://www.instagram.com/explore/tags/{hashtag:s}/?__a=1"
        log.info(f"retrieving images for #{hashtag:s}...")

        return requests.get(url, allow_redirects=False)

    def _get_posts(self) -> set[dict[str, Any]]:
        try:
            response = self._get_page(self.hashtag)
        except requests.exceptions.RequestException as e:
            log.error(e)
            return set()

        try:
            reply = response.json()
        except requests.exceptions.JSONDecodeError as e:
            log.error(e)
            return set()

        if self.scrapfly_key is not None:
            try:
                content = reply["result"]["content"]
            except KeyError as e:
                log.error(e)
                return set()

            try:
                reply = json.loads(content)
            except json.JSONDecodeError as e:
                log.error(e)
                return set()

        try:
            node_container_list = reply["graphql"]["hashtag"]["edge_hashtag_to_media"]["edges"]
            new_posts = set()
            for container in node_container_list:
                if (node := container.get("node")) is None or node.get("is_video", True) or node.get("taken_at_timestamp", -1) < self.started_at:
                    continue

                # "https://instagram.ftxl3-1.fna.fbcdn.net/v/t51.2885-15/284866407_106157872074214_6314192356252402153_n.jpg?stp=dst-jpg_e35&_nc_ht=instagram.ftxl3-1.fna.fbcdn.net&_nc_cat=110&_nc_ohc=Og8G8GLwqZgAX882Aft&edm=ABZsPhsBAAAA&ccb=7-5&oh=00_AT_KlEEkb6oLhAr4eohHPH60DP7mBsXoesP2WPd7jXTyjg&oe=629C4D17&_nc_sid=4efc9f"
                if (image_url := node.get("display_url")) is None or image_url in self.processed:
                    continue

                new_posts.add(node)

            return new_posts

        except KeyError as e:
            log.error(e)
            return set()

    def _get_image_urls(self, nodes: set[dict[str, Any]]) -> list[str]:
        no_nodes = 0
        posts = list()
        # take the latest self.post_limit posts during this iteration and add them to the queue
        for each_node in sorted(nodes, key=lambda x: x["taken_at_timestamp"], reverse=True):
            if no_nodes >= self.post_limit >= 0:
                log.warning(f"reached post limit of {self.post_limit:d}.")
                break

            image_url = each_node["display_url"]

            log.info(f"adding image '{image_url:s}' to print queue")
            posts.insert(0, image_url)
            no_nodes += 1

        return posts

    def _process_urls(self, image_urls: list[str]):
        for each_url in image_urls:
            log.info(f"printing {each_url:s}...")
            self._print_photo(each_url)
            self.processed.add(each_url)

    def print_new_images(self):
        if len(self.hashtag) < 1:
            log.info("no hashtag set")
            return

        if self.post_limit < 1:
            log.info("post limit is below one.")
            return

        posts = self._get_posts()
        log.info(f"found {len(posts):d} new images")

        image_urls = self._get_image_urls(posts)
        log.info(f"processing {len(image_urls):d} images total")

        self._process_urls(image_urls)


def get_config() -> dict[str, Any]:
    log.info("reading config file...")
    with open("config.json", mode="r") as file:
        return json.load(file)


def clean_hashtag(hashtag: str) -> str:
    return "".join(x for x in hashtag if x in string.digits + string.ascii_letters)


def main():
    image_bot = ImageBot()

    while True:
        # read config
        config = get_config()

        image_bot.scrapfly_key = config.get("scrapfly_key")
        image_bot.hashtag = clean_hashtag(config.get("hashtag"))
        image_bot.post_limit = config.get("post_limit")

        frame_path = config.get("frame_path")

        # get latest image
        image_bot.print_new_images()

        delay_range = config.get("delay_range_ms")
        random_delay = random.uniform(min(delay_range), max(delay_range))
        log.info(f"waiting for {round(random_delay):d} ms...")
        time.sleep(random_delay / 1_000)


if __name__ == "__main__":
    main()
