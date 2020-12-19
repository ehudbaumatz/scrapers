import logging
from datetime import datetime
from typing import FrozenSet, List
from abc import ABC

from browser import Browser
from request import proxy_request, get_request, get_proxy_api_key
from lxml import html
from cachier import cachier
import re
from tqdm import tqdm


class Spider(ABC):

    def __init__(self, name, request_method):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.get = request_method

    @cachier(cache_dir='cache')
    def query(self, queries: FrozenSet[str], hide_progress_bar: bool = False):
        raise Exception('Not Implemented')

    def get_name(self):
        return self.name


class GoogleWebSpider(Spider):

    def __init__(self, name='google', request_method=proxy_request):
        super().__init__(name, request_method)

    @cachier()
    def query(self, queries: FrozenSet[str], hide_progress_bar: bool = False):

        results = []
        for q in tqdm(queries, disable=hide_progress_bar):
            try:
                rsp = self.get(q)
                results.extend([q, u] for u in self.parse(rsp.text))
            except Exception as ex:
                self.logger.error(ex)
        return results

    @staticmethod
    def parse(text: str):
        doc = html.fromstring(text.encode('utf-8'))
        return [a.get('href') for a in doc.cssselect('a') if
                'href' in a.attrib and a.get('href').startswith('http') and 'google' not in a.get('href')]


class FeedspotSpider(Spider):

    def __init__(self, name='feedspot', request_method=get_request):

        super().__init__(name, request_method)

    @cachier()
    def query(self, queries: FrozenSet[str], hide_progress_bar: bool = False):

        results = []
        for q in tqdm(queries, disable=hide_progress_bar):
            try:
                results.extend([q, rsp] for rsp in self.parse(self.get(q).text))
            except Exception as ex:
                self.logger.error(ex)
        return results

    def parse(self, text: str):
        doc = html.fromstring(text.encode('utf-8'))
        return [a.get('href') for a in doc.cssselect('a.ext')]


class WaybackSpider(Spider):

    def __init__(self, name='wayback', request_method=proxy_request):
        super().__init__(name, request_method)

        self.template = 'http://web.archive.org/web/{0}/{1}'
        self.page = 'http://web.archive.org/cdx/search/cdx?url={}&collapse=original&filter=statuscode:200&filter=mimetype:text/html&page={}'
        self.page_num = 'http://web.archive.org/cdx/search/cdx?url={domain}&collapse=original&filter=statuscode:200&filter=mimetype:text/html&showNumPages=true'
        columns = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]
        self.field_count = len(columns)
        self.pattern = re.compile(':80|/amp/')

    @cachier()
    def query(self, queries: FrozenSet[str], hide_progress_bar: bool = False):

        results = []
        for q in tqdm(queries, disable=hide_progress_bar):
            try:

                n_pages = int(self.get(self.page_num.format(q)).text.strip())
                rsp = self._get_pages(q, n_pages)
                results.append([q, rsp])
            except Exception as ex:
                self.logger.error(ex)
        return results

    def parse(self, text: str):

        for line in text.split('\n'):
            fields = line.split(' ')
            if len(fields) == self.field_count and len(re.findall(self.pattern, fields[2])) == 0:
                yield f'http://web.archive.org/web/{fields[1]}/{fields[2]}'

    def _get_pages(self, domain, n_pages):

        results = []
        for i in range(n_pages):
            try:
                for u in self.parse(self.get(self.page.format(domain, i))):
                    results.extend(u)

            except Exception as ex:
                self.logger.error(ex)
        return results


class BrowserSpider(ABC):

    def __init__(self, name, executable_path: str = 'chromedriver', proxy: str = None):
        self.browser = Browser(executable_path, proxy)
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

    @cachier(cache_dir='cache')
    def query(self, queries: FrozenSet[str], hide_progress_bar: bool = False):
        raise Exception('Not Implemented')

    def get_name(self):
        return self.name


class GoogleImageSpider(BrowserSpider):

    def __init__(self, proxy: str, executable_path: str = './chromedriver', path:str =None):

        super().__init__('google_image_spider', executable_path, proxy)
        self.pattern = re.compile(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)')
        self.pattern2 = re.compile(r'\<|\>')
        self.template = 'https://www.google.com/search?q={}&tbm=isch&hl=en&chips=q:{},online_chips:{}'
        self.button_css = 'input[type="button"]'
        self.visited = set()
        self.tbnids = list()
        self.path = f'images_batch_{datetime.now()}.txt' if path is None else path
        self.image_count = 0
        self.total_image_count = 0

    @cachier(cache_dir='cache')
    def query(self, queries: FrozenSet[str], hide_progress_bar: bool = False):

        urls = list(queries)
        pbar = tqdm(desc=f'starting main loop on {len(urls)} urls')
        while len(urls) > 0:
            pbar.update()

            url = urls.pop()
            self.browser.browse(url)
            sh = self.browser.get_scroll_height() # should be zero
            clicked = False

            while True:
                self.parse()

                csh = self.browser.scroll_down()
                if csh == sh and not clicked:
                    self.browser.click(self.button_css)
                    clicked=True
                elif csh != sh:
                    sh = csh
                else:
                    break

            for related in self.click_related_images(url):
                urls.extend(related)

            pbar.set_description(f'colleted {self.image_count} images on page, total images collected: {self.total_image_count}')

    def click_related_images(self, url:str):
        related = []
        pbar = tqdm(desc=f'starting looping data ids')
        while len(self.tbnids):
            pbar.update()
            data_id = self.tbnids
            self.visited.add(data_id)
            self.browser.browse(f'{url}#imgrc={data_id}')
            if '#imgrc' not in self.browser.driver.current_url:
                continue

            _,_, doc = self.parse()
            related.extend([f'https://www.google.com/{a.get("href")}' for a in doc.cssselect('a') if
                   'aria-label' in a.attrib and 'Related imges' in a.get('aria-label')])
        return related

    def _get_data_ids(self, doc):
        ids = []
        for div in doc.cssselect('div'):
            atrib = div.attrib
            if 'jsaction' in atrib and 'data-tbnid' in atrib and atrib['data-tbnid'] not in self.visited:
                ids.append(atrib['data-tbnid'])
        return ids

    def _get_images(self, text):
        return [img for img in re.findall(self.pattern, text) if
                  (len(re.findall(self.pattern2, img)) == 0) and img.startswith('http') and img not in self.visited]

    def parse(self):
        text = self.browser.driver.page_source.encode('utf-8').decode('utf-8')
        doc = html.fromstring(text)
        ids = self._get_data_ids(doc)
        images = self._get_images(text)

        self.tbnids.extend(ids)
        self._write(images)
        return ids, images, doc

    def _write(self, data:List[str]):

        ix = 0
        with open(self.path, 'a+') as f:
            for ix, item in enumerate(data):
                self.visited.add(item)
                f.write(f'{item}\n')
        self.image_count += ix




