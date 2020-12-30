import logging
from datetime import datetime
from typing import FrozenSet, List
from abc import ABC


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

def test():
    spider=GoogleWebSpider()
    qs = frozenset([f'https://www.google.com/search?q={s} site:https://blog.feedspot.com/' for s in ['Auto Body Styles', 'Commercial Trucks']])
    spider.query(qs)




