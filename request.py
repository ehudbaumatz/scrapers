import requests
import fake_useragent
import os

def get_proxy_service_url():

    return os.environ.get('PROXY_SERVICE')

def proxy_request(url):
    return get_request(url, {'https': get_proxy_service_url(), 'http':get_proxy_service_url()})

def get_request(url, proxies=None):

    headers_get = {
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
    headers_get["User-Agent"] = user_agent


    rsp = requests.get(url, verify=False, headers=headers_get, proxies=proxies)
    return rsp

