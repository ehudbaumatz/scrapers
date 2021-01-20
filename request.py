import requests
import os
from scraper_api import ScraperAPIClient
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession


def get_proxy_api_key():
    return os.environ.get('PROXY_API_KEY')


def proxy_request(url):
    client = ScraperAPIClient(os.environ.get('PROXY_API_KEY'))
    rsp = client.get(url=url)
    return rsp


def get_request(url):
    rsp = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'})
    return rsp


def batch(urls, proxies=None, hooks=None, max_workers=10):

    with FuturesSession(max_workers=max_workers) as session:
        futures = [session.get(url, proxies=proxies, hooks=hooks, timeout=10) for url in urls]
        for future in as_completed(futures, timeout=10):
            response = future.result()
            yield response




