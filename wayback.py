import csv
import logging
from pathlib import Path
from typing import Dict

import click
import re
import requests
from request import batch
from tqdm import tqdm
import itertools as it

HEADERS: Dict[str, str] = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
CDX_SERVER = 'http://web.archive.org/cdx/search/cdx'


def clean(df, threshold=5):
    sz = df.url.value_counts()
    df = df[df.url.isin(sz[sz < threshold].index)]
    df.drop_duplicates('url', inplace=True)
    return df


def get_page_count(domain):
    url = f'{CDX_SERVER}?url={domain}&collapse=original&filter=statuscode:200&filter=mimetype:text/html&showNumPages=true'
    response = requests.get(url, headers=HEADERS)
    return int(response.text.strip())


def get_waybacks_urls(domains, proxies, max_pages=100, max_workers=10):
    urls = [
        f'{CDX_SERVER}?url={domain}/*&collapse=original&filter=statuscode:200&filter=mimetype:text/html&showNumPages=true'
        for domain in domains]

    bar = tqdm(total=len(urls))
    for response in (batch(urls, proxies, max_workers=max_workers)):
        try:
            bar.update()
            domain = response.url[42:].split('&')[0]
            limit = min(int(response.text.strip()), max_pages)
            urls = [
                f'{CDX_SERVER}?url={domain}&collapse=original&filter=statuscode:200&filter=mimetype:text/html&page={i}'
                for i in range(limit)]
            yield urls
        except Exception as ex:
            print(ex)


def download_wayback_urls(urls, proxies, max_workers=10):
    pat = re.compile(':80|/amp/')
    template = 'http://web.archive.org/web/{0}/{1}'
    columns = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]
    field_count = len(columns)

    for response in batch(urls, proxies, max_workers=max_workers):
        try:
            for line in response.text.split('\n'):
                fields = line.split(' ')
                if len(fields) == field_count and len(re.findall(pat, fields[2])) == 0:
                    url = template.format(fields[1], fields[2])
                    yield [response.url, url, fields[2]]
        except Exception as ex:
            print(ex)



@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
@click.argument('key', envvar='PROXY_API_KEY')
def main(key, input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)

    proxies = {
        "http": f"http://scraperapi:{key}@proxy-server.scraperapi.com:8001",
        "https": f"http://scraperapi:{key}@proxy-server.scraperapi.com:8001"
    }

    # read list of domains
    domains = [line.strip() for line in open(input_filepath)]
    logger.info(f'making final data set from {len(domains)} domains')
    urls = list(it.chain.from_iterable([urls for urls in get_waybacks_urls(domains, proxies)]))
    logger.info(f'starting downloading {len(urls)} domains')

    writer = csv.writer(open(output_filepath, 'w'), delimiter='\t')
    bar = tqdm(total=len(urls))
    with open(output_filepath, 'a+') as f:
        for response in download_wayback_urls(urls, proxies):
            bar.update()
            writer.writerow(response)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    import sys

    main()
