import re
from datetime import datetime
from typing import List

from selenium import webdriver
from tqdm import tqdm

from browser import get_proxy, get_scroll_height, scroll_down, click

from lxml import html

pattern = re.compile(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)')
pattern2 = re.compile(r'\<|\>')
template = 'https://www.google.com/search?q={}&tbm=isch&hl=en&chips=q:{},online_chips:{}'
button_css = 'input[type="button"]'
visited = set()
tbnids = list()
path = f'images_batch_{datetime.now()}.txt'
image_count = 0
total_image_count = 0

def search(queries: List[str], executable_path: str = './chromedriver', proxy: str = None):


    service = webdriver.chrome.service.Service(executable_path=executable_path)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument("window-size=1920,1080")
    options = options.to_capabilities()
    proxy = get_proxy(proxy) if proxy is not None else None
    driver = webdriver.Remote(service.service_url, options, proxy=proxy)


    urls = list(queries)
    pbar = tqdm(desc=f'starting main loop on {len(urls)} urls')
    while len(urls) > 0:
        pbar.update()

        url = urls.pop()
        driver.get(url)
        sh = 0 # get_scroll_height(driver) # should be zero
        clicked = False

        while True:
            try:
                parse(driver)

                csh = scroll_down(driver)
                if csh == sh and not clicked:
                    click(driver, button_css)
                    clicked=True
                elif csh != sh:
                    sh = csh
                else:
                    break

            except Exception as ex:
                print(ex, url)

        urls.extend(click_related_images(driver, url))
        pbar.set_description(f'collected {image_count} images on page, total images collected: {total_image_count}')


def click_related_images(driver: webdriver, url:str):
    related = []
    pbar = tqdm(desc=f'starting looping on {len(tbnids)} data ids')
    while len(tbnids):
        pbar.update()
        data_id = tbnids.pop()
        pbar.set_description(f'left {len(tbnids)} data ids to process')
        visited.add(data_id)
        driver.get(f'{url}#imgrc={data_id}')
        if '#imgrc' not in driver.current_url:
            continue

        # _,_, doc = parse(driver)
        text = driver.page_source.encode('utf-8').decode('utf-8')
        doc = html.fromstring(text)
        l = [f'https://www.google.com/{a.get("href")}' for a in doc.cssselect('a') if
               'aria-label' in a.attrib and 'Related images' in a.get('aria-label')]
        if len(l) > 0:
            rel = l[0]
            if rel.startswith('http'):
                related.append(rel)
    return related


def get_data_ids(doc):
    ids = []
    for div in doc.cssselect('div'):
        atrib = div.attrib
        if 'jsaction' in atrib and 'data-tbnid' in atrib and atrib['data-tbnid'] not in visited:
            ids.append(atrib['data-tbnid'])
    return ids


def get_images(text):
    return [img for img in re.findall(pattern, text) if
              (len(re.findall(pattern2, img)) == 0) and img.startswith('http') and img not in visited]


def parse(driver: webdriver):
    text = driver.page_source.encode('utf-8').decode('utf-8')
    doc = html.fromstring(text)
    ids = get_data_ids(doc)
    images = get_images(text)

    tbnids.extend(ids)
    write(images)
    return ids, images, doc


def write(data:List[str]):

    ix = 0
    with open(path, 'a+') as f:
        for ix, item in enumerate(data):
            visited.add(item)
            f.write(f'{item}\n')

    # image_count += ix


import os

queries = [f'https://www.google.com/search?q=jewelry+image+retouching+before+after&tbm=isch&chips=q:jewelry+image+retouching+before+after,online_chips:{item}&hl=en&sa=X&ved=2ahUKEwi9g7P9vt3tAhXM0YUKHbh8CWgQ4lYoBnoECAEQHw&biw=1745&bih=860' for item in ['ring', 'silver', 'gold', 'necklace', 'diamond', 'clipping+path', 'photo+retouching+service']]
search(queries, proxy=os.environ.get('PROXY_URL'))
