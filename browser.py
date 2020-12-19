import logging
import time
import urllib.parse

from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver import Proxy
from selenium.webdriver.common.proxy import ProxyType

# import fire
import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm


class Browser(object):

    def __init__(self, executable_path: str = 'chromedriver', proxy: str = None):

        service = webdriver.chrome.service.Service(executable_path=executable_path)
        service.start()
        options = webdriver.ChromeOptions()
        options.add_argument("window-size=1920,1080")
        options = options.to_capabilities()
        proxy = self._get_proxy(proxy) if proxy is not None else None
        self.driver = webdriver.Remote(service.service_url, options, proxy=proxy)

    @staticmethod
    def _get_proxy(proxy_url: str):

        proxy = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': proxy_url,
            'ftpProxy': proxy_url,
            'sslProxy': proxy_url,
            'noProxy': 'localhost'  # set this value as desired
        })
        return proxy

    def _wait_page_load(self):
        # wait on load page complete
        wait = WebDriverWait(self.driver, 10, poll_frequency=1)
        wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

    def browse(self, url: str):
        self.driver.get(url)
        self._wait_page_load()

    def click(self, css: str):
        try:
            element = WebDriverWait(self.driver, 10, poll_frequency=1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
            element.click()
            self._wait_page_load()
        except Exception as ex:
            print(ex)

    def get_scroll_height(self):
        return self.driver.execute_script(
            "var lenOfPage=document.body.scrollHeight;return lenOfPage;")

    def scroll_down(self, wait:bool=True):
        sh = self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        if wait:
            self._wait_page_load()
        return sh

    def scroll_to_bottom(self):

        sh = self.scroll_down()
        while True:
            csh = self.scroll_down()
            if csh == sh:
                break
            sh = csh

# proxy_url = 'http://scraperapi:e16acd19f0bfd74cfeb9202d0092ad42@proxy-server.scraperapi.com:8001'
# service = webdriver.chrome.service.Service(executable_path='./chromedriver')
# service.start()
# options = webdriver.ChromeOptions()
# options.add_argument("window-size=1920,1080")
# proxy = Proxy({
#             'proxyType': ProxyType.MANUAL,
#             'httpProxy': proxy_url,
#             'ftpProxy': proxy_url,
#             'sslProxy': proxy_url,
#             'noProxy': 'localhost'  # set this value as desired
#         })
# # options.add_argument('--proxy-server=%s' % proxy)
# options = options.to_capabilities()
# driver = webdriver.Remote(service.service_url, options, proxy=proxy)
# driver.get('https://www.google.com/search?q=jewelry+image+retouching+before+after&tbm=isch&hl=en&chips=q:jewelry+image+retouching+before+after,online_chips:{}&sa=X&ved=2ahUKEwijrayPs9jtAhVH0oUKHT_SD_sQ4lYoBXoECAEQHg&biw=1527&bih=833#imgrc=KDzdDfsF8aj-nM'.format('ring'))
# wait = WebDriverWait(driver, 10, poll_frequency=1)
# wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
# print('end')

# def mix(fn, url, bcss, css, driver_loc, limit=10000):
#     fpbar = tqdm()
#     limit = int(limit)
#     driver = get_browser(driver_loc)
#
#     r = urllib.parse.urlparse(url)
#     base = '{}://{}'.format(r.scheme, r.netloc)
#
#     links = set()
#     driver.get(url)
#
#     html = driver.page_source.encode('utf-8')
#     doc = etree.fromstring(html, etree.HTMLParser())
#     links.update([a.get('href') for a in doc.cssselect(css)])
#
#     try:
#         element = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, bcss)))
#         element.click()
#     except Exception as ex:
#         print(ex)
#
#     time.sleep(5)
#     last_height = 0  # driver.execute_script("return document.body.scrollHeight")
#
#     i = 0
#     while i < limit:
#         fpbar.update(1)
#
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(4)
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break
#         last_height = new_height
#         i += 1
#
#     html = driver.page_source.encode('utf-8')
#     doc = etree.fromstring(html, etree.HTMLParser())
#     links.update([a.get('href') for a in doc.cssselect(css)])
#     logging.info('found {} links'.format(len(links)))
#     with open(fn, 'a+') as f:
#         for s in links:
#             if s is None:
#                 continue
#             if not s.startswith('http'):
#                 s = base + s
#             f.write(s + '\n')
#     fpbar.close()
# def more(fn, url, bcss, acss, driver_loc, limit=10000):
#     pbar = tqdm()
#     links = set()
#     page_size = 1000
#     limit = int(limit)
#     r = urllib.parse.urlparse(url)
#     base = '{}://{}'.format(r.scheme, r.netloc)
#     driver = get_browser(driver_loc)
#
#     driver.get(url)
#     #
#     # html = driver.page_source.encode('utf-8')
#     # doc = etree.fromstring(html, etree.HTMLParser())
#     # links.update([a.get('href') for a in doc.cssselect(acss)])
#
#     try:
#         scroll_to_bottom(driver)
#         element = WebDriverWait(driver, 20).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, bcss)))
#     except Exception as ex:
#         print(ex)
#         return
#
#     i, size = 0, 0
#     while driver.find_elements_by_css_selector(bcss) and i < limit:
#         pbar.update(1)
#         i += 1
#
#         urls = get_links(acss, driver)
#         if len(urls) == 0 or all(u in links for u in urls): break
#         links.update(urls)
#
#         element.click()
#
#         try:
#             scroll_to_bottom(driver)
#             element = WebDriverWait(driver, 20).until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR, bcss)))
#         except Exception as ex:
#             print(ex)
#             break
#
#     logging.info('found {} links'.format(len(links)))
#     with open(fn, 'a+') as f:
#         for s in links:
#             if s is None:
#                 continue
#             if not s.startswith('http'):
#                 s = base + s
#             f.write(s + '\n')
#     pbar.close()
# def paging2(fn, css, template, driver_loc, limit=10000):
#     pbar = tqdm()
#     limit = int(limit)
#     r = urllib.parse.urlparse(template.format(1))
#     base = '{}://{}'.format(r.scheme, r.netloc)
#
#     links = set()
#
#     driver = get_browser(driver_loc)
#
#     page = 0
#     while page < limit:
#         try:
#             page += 1
#             pbar.update(1)
#             url = template.format(page)
#             driver.get(url)
#
#             try:
#                 element = WebDriverWait(driver, 10).until(
#                     EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
#             except Exception as ex:
#                 print(ex)
#
#             urls = get_links(css, driver)
#             if len(urls) == 0 or all(u in links for u in urls): break
#             links.update(urls)
#
#         except Exception as ex:
#             print(ex)
#     pbar.close()
#     logging.info('found {} links'.format(len(links)))
#     with open(fn, 'a+') as f:
#         for s in links:
#             if s == None: continue
#             if not s.startswith('http'): s = base + s
#             f.write(s + '\n')
# def get_links(css, driver):
#     html = driver.page_source.encode('utf-8')
#     doc = etree.fromstring(html, etree.HTMLParser())
#     urls = [a.get('href') for a in doc.cssselect(css)]
#     return urls
# def paging(fn, css, template, limit=100000):
#     pbar = tqdm()
#     limit = int(limit)
#     r = urllib.parse.urlparse(template.format(1))
#     base = '{}://{}'.format(r.scheme, r.netloc)
#
#     links = set()
#     page = 0
#     while page < limit:
#         try:
#             page += 1
#             pbar.update(1)
#             url = template.format(page)
#             rsp = requests.get(url, headers={
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}, timeout=5)
#
#             doc = etree.fromstring(rsp.text, etree.HTMLParser())
#             if doc is None: continue
#             urls = [a.get('href') for a in doc.cssselect(css)]
#             if (len(urls) == 0 or all(u in links for u in urls)) and page > 1: break
#             #     if ~changed : break
#             #     else: changed = False
#             # else:
#             #     changed = True
#
#             links.update(urls)
#
#         except Exception as ex:
#             print(ex)
#     pbar.close()
#     logging.info('found {} links'.format(len(links)))
#     with open(fn, 'a+') as f:
#         for s in links:
#             if s == None: continue
#             if not s.startswith('http'): s = base + s
#             f.write(s + '\n')
# def infinite(fn, url, css, driver_loc, limit=100000):
#     pbar = tqdm()
#     limit = int(limit)
#     driver = get_browser(driver_loc)
#
#     r = urllib.parse.urlparse(url)
#     base = '{}://{}'.format(r.scheme, r.netloc)
#
#     links = set()
#     driver.get(url)
#     time.sleep(5)
#     last_height = 0  # driver.execute_script("return document.body.scrollHeight")
#     i = 0
#     while i < limit:
#         i += 1
#         pbar.update(1)
#
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(10)
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         if new_height == last_height:
#             break
#         last_height = new_height
#
#     html = driver.page_source.encode('utf-8')
#     doc = etree.fromstring(html, etree.HTMLParser())
#     links.update([a.get('href') for a in doc.cssselect(css)])
#     logging.info('found {} links'.format(len(links)))
#     with open(fn, 'a+') as f:
#         for s in links:
#             if s == None: continue
#             if not s.startswith('http'): s = base + s
#             f.write(s + '\n')
#     pbar.close()


# if __name__ == '__main__':
#     pass
# log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# logging.basicConfig(level=logging.INFO, format=log_fmt)
# # paging('test.url', 'article > h2 > a', 'https://www.washingtontimes.com/topics/social-issues/186/t/stories/?page={}', limit=4000)
#
# queries =['Non-alcoholic beverages', 'Paranormal phenomena', 'Arts and crafts', 'Birdwatching', 'Comic books', 'Puzzle games', 'Gardening', 'Diseases', 'Injury', 'Alternative music', 'Hip hop music', 'News/Talk radio stations', 'National Public Radio', 'Shops', 'College football', 'Disabled sports', 'Rugby', 'Soccer', 'Oral care', 'Reality television stars', 'Science fiction television shows', 'Adventure video games', 'Puzzle computer and video games']
#
#
# links = scrape_google(queries, 'missing.csv', prefix='category ', suffix=' site:https://en.wikipedia.org')
# print(links)

# ch = '../../usr/bin/chromedriver'
# bcss = 'div.buttons button'
# css = 'div.text-center > a'
# url = 'https://www.cosmetictown.com/news'
# infinite('test_mediom.txt', 'https://medium.com/topic/remote-work', 'h3 > a', '../../chromedriver')

# mix('test.url', url, bcss, css,'../../chromedriver')
# css = 'ul > li > div > div > a'
# url = 'https://www.theguardian.com/society/sexual-health/?page={}'
# paging('test.url', css, url)
# infinite('test.url','https://rewire.news/primary-topic/abortion/','article > h3 > a','../../chromedriver')
# more('drugs.url', 'https://www.vice.com/en_us/section/drugs', 'button.loading-lockup-infinite__button',
#       'div.vice-card__content > h3 > a', '../../chromedriver')
# paging('test.url', 'div.entry-header > h3 > a', 'https://nypost.com/tag/tragedy/page/{}/')
# #
# bad = ['https://web.archive.org/web/20180227232841/https://www.nbcnews.com/health/sexual-health']
# #
# for url in bad:
#     css = selector(url, '../../chromedriver', None)

# import time
# import csv
# writer = csv.writer(open('google_results.csv', 'w'))
# links = []
# service = webdriver.chrome.service.Service(executable_path='../../chromedriver')
# service.start()
# options = webdriver.ChromeOptions()
# options.add_argument("window-size=1920,1080")
# options = options.to_capabilities()
# driver = webdriver.Remote(service.service_url, options)

# fire.Fire()

# 'https://thefullpint.com/beer-news/' 'https://globalnews.ca/tag/drug-addiction/', 'http://www.glamour.com/about/sexual-health', 'http://www.theguardian.com/society/sexual-health?page=6'
# url = 'http://insider.foxnews.com/tag/lgbt'  #https://theconversation.com/us/topics/substance-abuse-2713 https://www.drugabuse.gov/news-events
# print(re.findall(header_tag, 'h3'))

# y = re.compile('\d{4}$')
# globals().update({'year': y})
# _diffbot('/Users/baumatz/Downloads/00001a7cf7654c34f300036c3b6eda51.json')
# with open('/Users/baumatz/Downloads/000026c715ccb4c7352465af98d289e') as f:
#     _diffbot(f, '', re.compile('\d{4}$'))
#
#
#     # dic = json.load(f)
# #
#
# sections('/Users/baumatz/python/allennlp/abortion-section', '/Users/baumatz/python/allennlp/abortion-section.csv', '/Users/baumatz/Documents/python/combo_guard/data/external/sites-cssselectors.csv')

# l = ['https://www.aljazeera.com/topics/categories/human_rights.html', 'http://www.huffingtonpost.com/topic/human-rights-campaign?page=2', 'https://www.shape.com/topics/plastic-surgery']
# for s in l:
#     css = selector(s, '../../chromedriver', None)
