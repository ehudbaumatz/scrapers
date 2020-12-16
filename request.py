import requests
import fake_useragent
import os
from scraper_api import ScraperAPIClient

def get_proxy_api_key():
    return os.environ.get('proxy_api_key')

def get_headers():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    ua = fake_useragent.UserAgent \
            (
            fallback='Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36')
    user_agent = ua.random
    headers["User-Agent"] = user_agent
    return headers


def proxy_request(url):
    client = ScraperAPIClient(get_proxy_api_key())
    rsp = client.get(url=url)
    return rsp

def get_request(url):

    rsp = requests.get(url, headers=get_headers())
    return rsp
