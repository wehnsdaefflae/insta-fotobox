# coding=utf-8
import json
import random

import time
from pathlib import Path
from typing import Any

import requests

import log


class ImageBot:
    def __init__(self, use_scrapfly: bool = True):
        self.hashtag = ""

        self.started_at = round(time.time())
        self.processed = set()
        self.queue = dict()

        self.image_dir = Path("images/")
        self.image_dir.mkdir(exist_ok=True)

        self.use_scrapfly = use_scrapfly
        if use_scrapfly:
            log.info("initializing (using scrapfly)...")
        else:
            log.info("initializing...")

    def _print_photo(self, image_url: str, image_id: str | None = None):
        image = requests.get(image_url)

        file_name = f"{self.hashtag:s}.jpg" if image_id is None else f"{image_id:s}.jpg"
        with open(self.image_dir / file_name, mode="wb") as file:
            file.write(image.content)

    def _update_queue(self):
        try:
            if self.use_scrapfly:
                url = f"https://api.scrapfly.io/scrape?key=f57deb2ee0e24a37883e09e7f204c645&url=https%3A%2F%2Fwww.instagram.com%2Fexplore%2Ftags%2F{self.hashtag:s}%2F%3F__a%3D1&tags=project%3Adefault&proxy_pool=public_residential_pool&asp=true"
            else:
                url = f"https://www.instagram.com/explore/tags/{self.hashtag:s}/?__a=1"

            log.info(f"retrieving images for #{self.hashtag:s}...")
            page = requests.get(url, allow_redirects=False)

        except requests.exceptions.RequestException as e:
            log.error(e)
            return

        try:
            reply = page.json()

        except requests.exceptions.JSONDecodeError as e:
            log.error(e)
            return

        if self.use_scrapfly:
            try:
                content = reply["result"]["content"]
            except KeyError as e:
                log.error(e)
                return

            try:
                reply = json.loads(content)
            except json.JSONDecodeError as e:
                log.error(e)
                return

        try:
            nodes = reply["graphql"]["hashtag"]["edge_hashtag_to_media"]["edges"]

        except KeyError as e:
            log.error(e)
            return

        log.info(f"found {len(nodes):d} images")
        for each_container in nodes:
            each_node = each_container["node"]

            if each_node.get("is_video", True) or each_node.get("taken_at_timestamp", -1) < self.started_at:             # false, 1653997832
                log.info("skipping post: is video or was taken before system startup")
                continue

            # "https://instagram.ftxl3-1.fna.fbcdn.net/v/t51.2885-15/284866407_106157872074214_6314192356252402153_n.jpg?stp=dst-jpg_e35&_nc_ht=instagram.ftxl3-1.fna.fbcdn.net&_nc_cat=110&_nc_ohc=Og8G8GLwqZgAX882Aft&edm=ABZsPhsBAAAA&ccb=7-5&oh=00_AT_KlEEkb6oLhAr4eohHPH60DP7mBsXoesP2WPd7jXTyjg&oe=629C4D17&_nc_sid=4efc9f"
            image_url = each_node.get("display_url", None)
            if image_url is None:
                log.info("skipping post: missing display_url")
                continue

            # "2850262858630868528"
            post_id = each_node.get("id", None)
            if post_id is None or post_id in self.processed:
                log.info("skipping post: missing post_id or already printed")
                continue

            log.info(f"adding image '{post_id:s}' to print queue")
            self.queue[post_id] = image_url

    def _process_queue(self):
        for each_id, each_url in sorted(tuple(self.queue.items()), key=lambda x: x[1]):
            log.info(f"printing {each_id:s}...")
            self._print_photo(each_url, image_id=each_id)
            self.processed.add(each_id)
            del(self.queue[each_id])

    def print_new_images(self):
        if self.hashtag is None:
            log.info("no hashtag set")
            return

        self._update_queue()
        self._process_queue()


def get_config() -> dict[str, Any]:
    log.info("reading config file...")
    with open("config.json", mode="r") as file:
        return json.load(file)


def main():
    image_bot = ImageBot(use_scrapfly=True)

    # remember all last images
    while True:
        # read config
        config = get_config()

        image_bot.hashtag = config.get("hashtag")
        delay_range = config.get("delay_range_ms")
        frame_path = config.get("frame_path")

        # get latest image
        image_bot.print_new_images()

        random_delay = random.uniform(min(delay_range), max(delay_range))
        log.info(f"waiting for {round(random_delay):d} ms...")
        time.sleep(random_delay / 1_000)


if __name__ == "__main__":
    main()
