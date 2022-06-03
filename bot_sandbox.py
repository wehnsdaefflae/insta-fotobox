# coding=utf-8
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from misc import get_config


def main():
    config = get_config()

    options = Options()
    # options.add_argument("start-maximized")

    driver_manager = ChromeDriverManager()
    executable_path = driver_manager.install()
    browser = webdriver.Chrome(service=Service(executable_path=executable_path), options=options)

    browser.implicitly_wait(5)

    browser.get("https://www.instagram.com/")

    browser.implicitly_wait(5)

    necessary_cookies = browser.find_element(by=By.XPATH, value="/html/body/div[4]/div/div/button[1]")
    necessary_cookies.click()

    time.sleep(5)

    user_name = browser.find_element(by=By.XPATH, value='//*[@id="loginForm"]/div/div[1]/div/label/input')
    password = browser.find_element(by=By.XPATH, value='//*[@id="loginForm"]/div/div[2]/div/label/input')

    user_name.send_keys(config["instagram_username"])
    password.send_keys(config["instagram_password"])
    password.submit()

    time.sleep(5)

    browser.get(f"https://www.instagram.com/explore/tags/{config['hashtag']:s}/")

    time.sleep(5)

    latest = browser.find_elements(by=By.XPATH, value='/html/body/div[1]/div/div[1]/div/div[1]/div/div/div[1]/div[1]/section/main/article/div[2]/div//img')

    time.sleep(5)

    for each in latest:
        print(each.get_property("src"))

    # By.CSS_SELECTOR

    browser.close()


if __name__ == "__main__":
    main()
