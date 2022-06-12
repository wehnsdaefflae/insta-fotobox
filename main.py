# coding=utf-8
from __future__ import annotations

import random
import subprocess
import time
from pathlib import Path

from PIL import Image

from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from webdriver_manager.chrome import ChromeDriverManager

from misc import get_config, clean_hashtag, save_image_from_url
import log


class InstaBot:
    def __init__(self, xpaths: dict[str, str]):
        self.xpaths = dict(xpaths)

        options = Options()
        options.add_argument("incognito")
        driver_manager = ChromeDriverManager()
        executable_path = driver_manager.install()
        service = Service(executable_path=executable_path)
        self.browser = webdriver.Chrome(service=service, options=options)

        self.browser.get(f"https://www.instagram.com/")
        self.browser.implicitly_wait(5)

    def clear(self):
        log.info("clearing notifications...")

        for each_path in self.xpaths.get("initial_clicks", []):
            target = self.browser.find_element(by=By.XPATH, value=each_path)
            target.click()
            time.sleep(5)

    def login(self, instagram_username: str, instagram_password: str):
        log.info("logging in...")

        while self.browser.current_url == "https://www.instagram.com/":
            username = self.browser.find_element(by=By.XPATH, value=self.xpaths["username"])
            username.send_keys(instagram_username)
            password = self.browser.find_element(by=By.XPATH, value=self.xpaths["password"])
            password.send_keys(instagram_password)
            time.sleep(1)

            password.submit()
            time.sleep(5)

    def get_image_urls(self, hashtag: str, scroll_to_end: int = 0) -> set[str]:
        self.browser.get(f"https://www.instagram.com/explore/tags/{hashtag:s}/")

        for i in range(scroll_to_end):
            time.sleep(5)
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.CONTROL + Keys.END)
            actions.perform()

        self.browser.implicitly_wait(5)
        xpath_image_container = self.xpaths["image_container"]
        latest = self.browser.find_elements(by=By.XPATH, value=xpath_image_container + "//img")

        return {each_child.get_property("src") for each_child in latest}

    def close(self):
        log.info("closing bot...")
        self.browser.close()

    # selenium on headless raspberry pi
    # https://stackoverflow.com/questions/25027385/using-selenium-on-raspberry-pi-headless


class ImagePrinter:
    def __init__(self, username: str, password: str, hashtag: str, xpaths: dict[str, str]):
        self.hashtag = hashtag
        self.bot = InstaBot(xpaths)
        self.bot.clear()
        self.bot.login(username, password)
        self.image_urls = set()

        self.images = Path("images")
        self.images.mkdir(exist_ok=True)

    def __enter__(self) -> ImagePrinter:
        initial_images = self.bot.get_image_urls(self.hashtag)
        self.image_urls.update(initial_images)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bot.close()

    def _print_image(self, image_url: str, frame_path: str | None):
        filename = self.images / f"{hash(image_url):d}.jpg"
        log.info(f"saving image to {filename.as_posix():s}...")
        save_image_from_url(filename, image_url)

        background = Image.open(filename)
        foreground = Image.open(frame_path)

        frame = foreground.resize(background.size)
        background.paste(frame, box=(0, 0), mask=frame.convert("RGBA"))
        filename_framed = filename.with_suffix("").as_posix() + "_framed.jpg"
        background.save(filename_framed)

        log.info(f"printing image {filename_framed:s}...")
        completed_process: subprocess.CompletedProcess = subprocess.run(["lp", filename_framed], capture_output=True, text=True)
        log.info(f"stdout: {completed_process.stdout:s}")
        log.error(f"stderr: {completed_process.stderr:s}")
        log.info(f"returncode: {completed_process.returncode:d}")

    def print_new_images(self, max_new_images: int, frame_path: str | None = None):
        image_urls = self.bot.get_image_urls(self.hashtag, scroll_to_end=1)
        new_urls = image_urls - self.image_urls
        log.info(f"found {len(new_urls):d} new images")

        for i, each_url in enumerate(new_urls):
            if i >= max_new_images:
                log.warning(f"stopped after {max_new_images:d} new images")
                break
            self._print_image(each_url, frame_path)
            self.image_urls.add(each_url)


def main():
    config = get_config("config.json")
    log.info("starting...")

    while True:
        with ImagePrinter(config["instagram_username"], config["instagram_password"], clean_hashtag(config["hashtag"]), config["xpaths"]) as printer:
            while True:
                printer.print_new_images(max_new_images=config["max_new_images"], frame_path=config["frame_path"])

                delay_range = config.get("delay_range_ms")
                random_delay = random.uniform(min(delay_range), max(delay_range)) / 1_000
                log.info(f"waiting for {round(random_delay):d} seconds...")
                time.sleep(random_delay)

                _config = get_config("config.json")
                if _config != config:
                    log.warning("config changed, restarting...")
                    config = _config
                    break


if __name__ == "__main__":
    main()
