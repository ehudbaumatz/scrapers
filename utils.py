import itertools
import logging
import os
import re
import json
from collections import defaultdict
from urllib.parse import urlparse, quote

import pandas as pd
import csv

# import fire
import requests
from lxml import etree, html
from lxml.cssselect import CSSSelector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm


# ---------------- HTML
def _get_css(e):
    css = e.tag

    if 'class' in e.attrib and len(e.get('class')) > 0:
        cls = e.get('class')
        return css + '.' + cls.strip().replace(' ', '.')
    if 'id' in e.attrib and len(e.get('id')) > 0:
        return css + '[id={}]'.format(e.get('id').strip())
    return None

def _path2css(path):
    """
    translates xpath to css selector
    :param path:
    :return:
    """
    css = ''
    for item in reversed(path):
        e, cls, id = item
        css += e.tag
        if cls: css += '.'+ cls.replace(' ', '.')
        elif id: css += '[id="{}"]'.format(id)

        css += ' '

    return css.strip()

def _get_identifiable_parent(p):

    """Climb up until element has class or id"""
    cls = p.get("class")
    id = p.get("id")
    path = [(p, cls, id)]
    while (cls is None and id is None):
        p = p.getparent()
        if p is None or 'body' in p.tag: return None

        cls = p.get("class")
        id = p.get("id")
        path.append((p, cls, id))
    css = _path2css(path)
    css += ' a'
    return (p, css)

def _get_mutual_parent(doc):

    def get_mutual_parents(elems):
        """Find mutual parent"""
        try:
            links = set([u.get('href') for p, u in elems])
            p = elems[0][0]
            childes = set([u.get('href') for u in p.cssselect('a')])

            while not childes.issuperset(links):

                p = p.getparent()
                childes = set([u.get('href') for u in p.cssselect('a')])
                # unique = is_unique(p)

            return p if p.tag not in ['body', 'html'] else None
        except Exception as ex:
            # logging.error(ex)
            return None

    def is_unique(e):
        css = _get_css(e)
        l = doc.cssselect(css)
        return len(l) == 1

    is_title = lambda x: x is not None and ((x.tag.startswith('h') and len(x.tag) == 2))

    urls = doc.cssselect('a')
    titles = [u for u in urls if (is_title(u.getparent())) or (len(u.getchildren()) >0 and is_title(u.getchildren()[0])) or 'class' in u.attrib ]
    if len(titles) > 3: urls = titles

    return [ _get_identifiable_parent(u) for u in urls]

    # for u in urls:
    #     try:
    #         p, css = get_identifiable_parent(u)
    #         d[css].append((p, u))
    #         # if p is not None and 'class' in p.attrib and len(p.get('class')) > 0: d[p.get('class')].append((p, u))
    #         # elif p is not None and 'id' in p.attrib: d[p.get('id')].append((p, u))
    #     except:
    #         pass

    # pairs = [(get_mutual_parents(pairs), (css, pairs)) for css, pairs in d.items() if len(pairs) > 3]
    # return pairs

def get_elements_size(driver, section_url, selectors):
    """Get the actual size of each element"""

    driver.get(section_url)
    try:
        element = WebDriverWait(driver, 10, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a")))
    except Exception as ex:
        logging.error(ex)
        return

    sizes = []
    for pcss, ccss in selectors:
        try:

            element = driver.find_element_by_css_selector(pcss)
            size = element.size['height'] * element.size['width']
            sizes.append((size, ccss))

        except Exception as ex:
            pass
                # logging.error(section_url)
                # logging.error(ex)
    return sizes

def element2css(element):
    """
    handles class and id tag to css query
    :param element:
    :return:
    """

    css = element.tag
    if 'id' in element.attrib: css+='#'+element.get('id').strip()
    # if 'class' in element.attrib: css+='.' + element.get('class').strip().replace(' ', '.')
    return css

keep = re.compile('h[0-9]')
skip = re.compile('footer|nav|menu|dropdown', re.IGNORECASE)

def get_text_from_subtree(c):
    """
    get text from element and all of its childs
    :param c:
    :return:
    """

    childes = c.getchildren()
    while len(childes)>0:
        c = childes[0]
        if c.text: return c.text.strip()
        childes = c.getchildren()
    return ''

def get_token_count(a):
    childes = a.getchildren()

    if 'title' in a.attrib:
        return  a.get('title').strip().count(' ')

    if len(childes) == 0:
        return a.text.strip().count(' ') if a.text else None

    l = sorted([get_text_from_subtree(c).count(' ') for c in childes ], reverse=True)
    return l[0] if len(l) > 0 else None

def copy_cssselector_ex(a, node=None, stop=False):
    """
    get css selector from a to root
    :param a:
    :param node:
    :param stop:
    :return:
    """

    path= []
    childs = a.getchildren()
    if len(childs) > 0:
        path.append(element2css(childs[0]))

    path.append(element2css(a))
    parent = a.getparent()
    while parent != node:
        css = element2css(parent)
        path.append(css)
        if ('.' in css or '#' in css) and stop: break
        parent = parent.getparent()

    return ' '.join(reversed(path))

def copy_cssselector(a, node=None):
    """
    get css selector from a to root
    :param a:
    :param node:
    :param stop:
    :return:
    """

    path= []
    childs = a.getchildren()
    if len(childs) > 0:
        path.append(element2css(childs[0]))

    path.append(element2css(a))
    parent = a.getparent()
    while parent != node:
        css = element2css(parent)
        path.append(css)
        parent = parent.getparent()

    return ' '.join(reversed(path))

def _get_urls_map(doc):
    """Traverse dom from each a tag to id'ed parent"""
    c2e = defaultdict(list)
    for a in doc.cssselect('a'):
        try:
            tokens = get_token_count(a)
            if tokens is None or tokens < 4 or 'href' not in a.attrib or len(a.get('href')) == 0 : continue

            css = copy_cssselector(a)
            c2e[css].append((a, tokens))
        except Exception as ex:
            print(ex)

    c2e = list(itertools.filterfalse(lambda p: len(p[1]) < 3, c2e.items())) #len(re.findall(skip, p[0])) > 0 or
    return c2e

def get_mutual_parent(elements):

    a = elements[-1][0]
    path = []
    if len(a.getchildren()) > 0:
        path.append(element2css(a.getchildren()[0]))

    path.append(element2css(a))

    parent = a.getparent()
    while parent is not None:

        if len(parent.getchildren()) >= len(elements):
            css = ' '.join(reversed(path))
            l = parent.cssselect(css)
            if css.endswith('a'):
                l = [a for a in l if get_token_count(a) is not None and get_token_count(a) >=4 and 'href' in a.attrib and len(a.get('href')) > 0 ]
            else:
                l = [a for a in l if get_token_count(a.getparent()) is not None and get_token_count(a.getparent()) >= 4 and 'href' in a.getparent().attrib    and len(a.getparent().get('href')) > 0]
            if len(l) == len(elements): return css, parent

        path.append(element2css(parent))
        parent = parent.getparent()

    return None, None

def longest_common_suffix(list_of_strings):
    reversed_strings = [' '.join(s.split()[::-1]) for s in list_of_strings]
    reversed_lcs = os.path.commonprefix(reversed_strings)
    lcs = ' '.join(reversed_lcs.split()[::-1])
    return lcs

def get_article_css(article):
    links = article.cssselect('a')
    if len(links) > 1:
        f = sorted([(get_token_count(a), a) for a in links if get_token_count(a)], key=lambda x: x[0], reverse=True)
        return copy_cssselector(f[0][1], article)
    else:
        return 'a'

def selector(url, driver_loc, css):

    service = webdriver.chrome.service.Service(executable_path=driver_loc)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options = options.to_capabilities()
    driver = webdriver.Remote(service.service_url, options)

    rsp = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'})
    doc = etree.fromstring(rsp.content, etree.HTMLParser())

    if css is not None:
        res = doc.cssselect(css)
        if len(res) > 0: return css

    # if we have proper html5 then just return
    articles = doc.cssselect('article')
    if len(articles) > 5:
        css = get_article_css(articles[3])
        return 'article ' + css

    articles = doc.cssselect('div.article')
    if len(articles) > 5:
        css = get_article_css(articles[3])
        return 'div.article ' + css

    c2e = _get_urls_map(doc)
    if len(c2e) == 0:
        return None
    if len(c2e) == 1:
        return c2e[0][0]

    p2c = []
    for c, es in c2e:
        try:
            css, parent = get_mutual_parent(es)
            if css is None: continue

            ix = c.find(css)
            till = c[:ix].strip()
            p2c.append((till, (c, sum(e[1] for e in es))))
        except Exception as ex:
            print(ex)

    csss = []
    for k, g in itertools.groupby(sorted(p2c, key=lambda x: x[0]), key=lambda x: x[0]):
        gp = sorted(list(g), key=lambda x: x[1][1], reverse=True)
        csss.append((k, gp[0][1][0]))

    if len(csss) > 1:
        rects = get_elements_size(driver, url, csss)
        size, g = next(itertools.groupby(sorted(rects, key=lambda x: x[0], reverse=True), key=lambda x: x[0]))
        g = list(g)
        if len(g) > 1:
            return longest_common_suffix([item[1] for item in g])
        else:
            return g[0][1]
    elif len(csss) == 1:
        return csss[0][1]
    else:
        return None