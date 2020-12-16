
import logging
from typing import List
from abc import ABC

from request import proxy_request, get_request
from lxml import html
from cachier import cachier

class Spider(ABC):

    def __init__(self, name, request_method):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.get = request_method

    @cachier()
    def query(self, queries: List[str]):
        raise Exception('Not Implemented')

    def get_name(self):
        return self.name

class GoogleWebSpider(Spider):

    def __init__(self):
        super().__init__('google', proxy_request)

    @cachier()
    def query(self, queries: List[str]):

        results = []
        for q in queries:
            try:
                rsp = self.parse(get(q))
                results.append([q, rsp])
            except Exception as ex:
                self.logger.error(ex)
        return results

    def parse(self, text:str):
        doc = html.fromstring(text.encode('utf-8'))
        return [a.get('href') for a in doc.cssselect('a') if 'google' not in a.get('href')]

class FeedspotSpider(Spider):

    def __init__(self):

        super().__init__('feedspot', get_request)

    @cachier()
    def query(self, queries: List[str]):

        results = []
        for q in queries:
            try:
                rsp = self.parse(self.get(q))
                results.append([q, rsp])
            except Exception as ex:
                self.logger.error(ex)
        return results

    def parse(self, text:str):
        doc = html.fromstring(text.encode('utf-8'))
        return [a.get('href') for a in doc.xpath('a.ext')]

import newspaper
if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]



    cosmo_paper = newspaper.build('https://www.cosmopolitan.com/', memoize_articles=False)
    categories= cosmo_paper.categories_to_articles()

    # for article in cosmo_paper.articles:
    #      print(article.url)

    for category in cosmo_paper.category_urls():
        print(category)
    cosmo_paper.categories_to_articles()




