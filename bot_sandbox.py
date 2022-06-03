# coding=utf-8
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from misc import get_config


class InstaBot:
    def __init__(self):
        self.config = get_config()

        options = Options()
        options.add_argument("incognito")

        driver_manager = ChromeDriverManager()
        executable_path = driver_manager.install()
        service = Service(executable_path=executable_path)
        self.browser = webdriver.Chrome(service=service, options=options)

        self.browser.implicitly_wait(5)

        self.browser.get(f"https://www.instagram.com/explore/tags/{self.config['hashtag']:s}/")

        self.browser.implicitly_wait(5)

    def clear(self):
        # --- starting clicks
        necessary_cookies = self.browser.find_element(by=By.XPATH, value="/html/body/div[4]/div/div/button[1]")
        necessary_cookies.click()
        time.sleep(5)

    def get_image_urls(self) -> set[str]:
        # --- getting image urls
        latest = self.browser.find_elements(by=By.XPATH, value='/html/body/div[1]/section/main/article/div[2]/div//img')

        time.sleep(5)

        return {each_child.get_property("src") for each_child in latest}

    def close(self):
        self.browser.close()

    # selenium on headless raspberry pi
    # https://stackoverflow.com/questions/25027385/using-selenium-on-raspberry-pi-headless


def main():
    insta_bot = InstaBot()
    insta_bot.clear()

    for i in range(10):
        image_urls = insta_bot.get_image_urls()
        print(image_urls)
        time.sleep(60)

    insta_bot.close()


if __name__ == "__main__":
    main()
