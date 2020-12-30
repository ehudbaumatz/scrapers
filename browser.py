# import fire
from selenium import webdriver
from selenium.webdriver import Proxy
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def browse(driver: webdriver, url: str):
    driver.get(url)
    wait_page_load(driver)


def click(driver: webdriver, css: str):
    try:
        element = WebDriverWait(driver, 10, poll_frequency=1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
        element.click()
        wait_page_load(driver)
    except Exception as ex:
        print(ex)


def get_scroll_height(driver: webdriver):
    return driver.execute_script(
        "var lenOfPage=document.body.scrollHeight;return lenOfPage;")


def scroll_down(driver: webdriver, wait: bool = True):
    sh = driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    if wait:
        wait_page_load(driver)
    return sh


def scroll_to_bottom(driver: webdriver):
    sh = scroll_down(driver)
    while True:
        csh = scroll_down(driver)
        if csh == sh:
            break
        sh = csh


def wait_page_load(driver):
    # wait on load page complete
    wait = WebDriverWait(driver, 10, poll_frequency=1)
    wait.until(lambda x: x.execute_script('return document.readyState') == 'complete')


def get_proxy(proxy_url: str):

    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_url,
        'ftpProxy': proxy_url,
        'sslProxy': proxy_url,
        'noProxy': 'localhost'  # set this value as desired
    })
    return proxy
