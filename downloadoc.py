import urllib3
from bs4 import BeautifulSoup


class DownloadDoc:

    def __init__(self, url: str='', config: dict={}):
        self._searched_links = []
        self._failed_links = []
        self._all_links = []
        self._doc_links = []
        self.error = ''
        self.config = self._default_config()
        self.config.update(config)

        if url != '':
            self.parse(url)

    def parse(self, url: str):
        """parse the url to get all of doc links"""
        http = urllib3.PoolManager()
        try:
            response = http.request('GET', url)
        except urllib3.exceptions.MaxRetryError:
            self.error = 'MaxRetryError'
            return

        if 499 > response.status > 399:
            self.error = 'Request Error' + str(response.status)
            return

        if response.status > 499:
            self.error = 'Server Error' + str(response.status)
            return

        if 'text/html' not in response.getheaders()['Content-Type']:
            self.error = 'Response Data Is Not Html Doc'
            return

        html = BeautifulSoup(response.data, features='html.parser')
        del response
        href_tags = html.findAll(href=True)
        for href_tag in href_tags:
            self._all_links.append(href_tag['href'])
            href = self._get_full_url(href_tag['href'], url)
            if href:
                self._searched_links.append(href)
                try:
                    response = http.request('HEAD', href, timeout=3, retry=2)
                except urllib3.exceptions.MaxRetryError:
                    self._failed_links.append(href)
                    continue

                for doc_type in self.config['doc_type']:
                    if doc_type in response.getheaders()['Content-Type']:
                        self._doc_links.append(href)

        return self.get_doc_links()

    def _get_full_url(self, href: str, url: str):
        try:
            href_object = urllib3.util.parse_url(href)
        except urllib3.exceptions.LocationParseError:
            self._failed_links.append(href)
            return

        if href_object.scheme:
            return href
        else:
            url_object = urllib3.util.parse_url(url)
            full_href = url_object.scheme + '://' + str(url_object.host)
            if url_object.port:
                full_href += url_object.port
            full_href = full_href + '/' + href
            return full_href

    def get_all_links(self):
        return self._all_links

    def get_doc_links(self):
        return self._doc_links

    def get_failed_links(self):
        return self._failed_links

    def get_searched_links(self):
        return self._searched_links

    def _default_config(self):

        return {
            'doc_type': ['word', 'pdf', 'excel']
        }


