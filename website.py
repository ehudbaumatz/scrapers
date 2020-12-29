import newspaper
from newspaper import Article
import csv

AGENT = 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1464.0 Safari/537.36'


class WebSite(object):
    def __init__(self, site, memoize_articles=False):

        self.site = site
        self.paper = newspaper.build(site, memoize_articles=memoize_articles,
                                     browser_user_agent=AGENT)

        self.purge_categories()
        self.purge_articles(self.paper.categories_to_articles())

    def purge_articles(self, articles):

        visited = set()
        self.paper.articles = []
        for a in articles:
            if a.url in visited: continue

            self.paper.articles.append(a)
            visited.add(a.url)

    def purge_categories(self):
        def language(category):
            a = Article(category.url)
            a.download(category.html)
            a.parse()
            return a.meta_lang

        self.paper.categories = [c for c in self.paper.categories if
                                 len(c.url) > len(self.site) and language(c).lower() == 'en']

    def dump(self, path, mode='a+'):

        self.paper.download_articles(threads=4)
        self.paper.parse_articles()
        writer = csv.writer(open(path, mode=mode))
        writer.writerow(['url', 'source_url', 'title', 'section', 'opinion', 'keywords', 'tags'])
        for a in self.paper.articles:
            try:
                section = a.meta_data['article']['section'] if 'article' in a.meta_data and 'section' in \
                                                                     a.meta_data['article'] else None
                opinion = a.meta_data['article']['opinion'] if 'article' in a.meta_data and 'opinion' in \
                                                                     a.meta_data['article'] else None
                writer.writerow([a.url, a.source_url, a.title, section, opinion, '|'.join(a.meta_keywords),
                                  '|'.join(a.tags)])
            except Exception as ex:
                print(ex)

