#!/usr/bin/python3 -u
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

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from misc import get_config, clean_hashtag, save_image_from_url
import log


class InstaBot:
    def __init__(self, xpaths: dict[str, str], debug: bool = False):
        self.xpaths = dict(xpaths)

        options = Options()
        options.add_argument("incognito")
        if not debug:
            options.add_argument("--headless")

        # requires: sudo apt-get install chromium-chromedriver
        executable_path = "D:/Eigene Dateien/Downloads/chromedriver_win32/chromedriver.exe" if debug else "/usr/lib/chromium-browser/chromedriver"
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
            password.submit()
            time.sleep(10)

    def get_image_urls(self, hashtag: str, scroll_to_end: int = 0) -> set[str]:
        self.browser.get(f"https://www.instagram.com/explore/tags/{hashtag:s}/")
        time.sleep(5)
        post_images = self.xpaths["post_images"]
        actions = ActionChains(self.browser)

        result = set()
        for i in range(scroll_to_end):
            log.info(f"scrolling to end ({i+1:d}/{scroll_to_end:d})...")
            actions.send_keys(Keys.CONTROL + Keys.END)
            actions.perform()
            time.sleep(5)
            all_images = set(self.browser.find_elements(by=By.XPATH, value=post_images))
            log.info(f"found {len(all_images):d} elements on page.")
            for image_element in all_images:
                image_url = image_element.get_property("src")
                result.add(image_url)

        log.info(f"found {len(result):d} new images total.")
        return result

    def close(self):
        log.info("closing bot...")
        self.browser.close()

    # selenium on headless raspberry pi
    # https://stackoverflow.com/questions/25027385/using-selenium-on-raspberry-pi-headless

    # alternative (also to webdriver_manager)
    # https://stackoverflow.com/questions/64979042/how-to-run-seleniumchrome-on-raspberry-pi-4
        # sudo apt-get install chromium-chromedriver


class ImagePrinter:
    def __init__(self, username: str, password: str, hashtag: str, xpaths: dict[str, str], debug: bool = False):
        self.hashtag = hashtag
        self.bot = InstaBot(xpaths, debug=debug)
        self.bot.clear()
        self.bot.login(username, password)
        self.ignore_posts = set()

        self.debug = debug

        self.images = Path("images")
        self.images.mkdir(exist_ok=True)

    def __enter__(self) -> ImagePrinter:
        log.info("retrieving existing images...")
        initial_images = self.bot.get_image_urls(self.hashtag, scroll_to_end=5)
        log.info(f"ignoring {len(initial_images):d} existing images.")
        self.ignore_posts.update(initial_images)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bot.close()

    def _print_image(self, image_url: str, frame_path: str | None, debug: bool = True):
        filename = self.images / f"{hash(image_url):d}.jpg"
        log.info(f"saving image to {filename.as_posix():s}...")
        save_image_from_url(filename, image_url)

        background = Image.open(filename)
        foreground = Image.open(frame_path)

        frame = foreground.resize(background.size)
        background.paste(frame, box=(0, 0), mask=frame.convert("RGBA"))
        filename_framed = filename.with_suffix("").as_posix() + "_framed.jpg"
        background.save(filename_framed)

        if True or debug:
            return

        log.info(f"printing image {filename_framed:s}...")
        completed_process: subprocess.CompletedProcess = subprocess.run(["lp", filename_framed], capture_output=True, text=True)
        log.info(f"stdout: {completed_process.stdout:s}")
        log.error(f"stderr: {completed_process.stderr:s}")
        log.info(f"returncode: {completed_process.returncode:d}")

    def print_new_images(self, max_new_images: int, frame_path: str | None = None):
        image_urls = self.bot.get_image_urls(self.hashtag, scroll_to_end=1)
        new_urls = {
            each_image_url
            for each_image_url in image_urls
            if each_image_url not in self.ignore_posts
        }
        log.info(f"found {len(new_urls):d} new images in {len(image_urls):d} retrieved images, "
                 f"ignoring {len(self.ignore_posts):d} images total")

        for i, each_image_url in enumerate(new_urls):
            if i >= max_new_images:
                log.warning(f"stopped after {max_new_images:d} new images")
                break

            print(f"printing image at {each_image_url:s}...")
            self._print_image(each_image_url, frame_path, debug=self.debug)

            self.ignore_posts.add(each_image_url)


def main():
    config = get_config("config.json")
    log.info("starting...")

    while True:
        username = config.get("instagram_username")
        password = config.get("instagram_password")
        hashtag = config.get("hashtag")
        is_debug = config.get("debug_system")

        if is_debug:
            log.critical("starting in DEBUG mode.")
        else:
            log.critical("starting in LIVE mode.")

        if username is None or password is None or hashtag is None:
            log.error("instagram_username, instagram_password, or hashtag not found in config.json, retrying in 10 "
                      "seconds...")
            time.sleep(10)
            config = get_config("config.json")
            continue

        with ImagePrinter(username, password, clean_hashtag(hashtag), config["xpaths"], debug=is_debug) as printer:
            while True:
                try:
                    printer.print_new_images(max_new_images=config["max_new_images"], frame_path=config["frame_path"])

                except StaleElementReferenceException as e:
                    printer.bot.browser.save_screenshot(f"stale_element_exception_{round(time.time() * 1_000):d}.png")
                    log.fatal(f"stale element exception: {e:s}")
                    raise e

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
