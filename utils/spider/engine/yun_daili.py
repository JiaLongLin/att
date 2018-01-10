#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import urllib
import urlparse

import requests
import bs4

LINKS = {
    'yun-daili': ['http://www.yun-daili.com/free.asp?stype=1',
                  'http://www.yun-daili.com/free.asp?stype=2',
                  'http://www.yun-daili.com/free.asp?stype=3',
                  'http://www.yun-daili.com/free.asp?stype=4']
}


class GetContext(object):
    def __init__(self):
        self.session = requests.session()
        self.links = LINKS.get('yun-daili')
        # self.ret = []

    def __del__(self):
        self.session.close()

    def do_collect(self):
        ret = []
        for url in self.links:
            start_url = self.get_start_url(url)
            context = self.get_context(url)
            list_nav = self.get_list_nav(context)
            while True:
                try:
                    params = list_nav.next()
                except StopIteration:
                    break
                context = self.get_context(start_url, params=params)
                ret += self.parser(context)
        return ret

    def get_context(self, url, params=None):
        if not params:
            req = self.session.get(url)
        else:
            req = self.session.get(url, params=params)
        return req.content

    @staticmethod
    def get_start_url(url):
        return urllib.splitquery(url)[0]

    @staticmethod
    def parser_params(href):
        return dict(urlparse.parse_qsl(href))

    def get_list_nav(self, context):
        soup = bs4.BeautifulSoup(context, 'html.parser')
        _div = soup.find('div', id='listnav')
        for link in _div.findAll('a'):
            href = link.get('href')
            yield self.parser_params(href[1:])

    @staticmethod
    def parser(context):
        soup = bs4.BeautifulSoup(context, 'html.parser')
        _list_div = soup.find('div', id='list')
        trs = _list_div.find('table').findAll('tr')
        ret = []
        try:
            for tr in trs[1:]:
                tds = tr.findAll('td')
                ip = tds[0].get_text()
                port = tds[1].get_text()
                ret.append({'ip': ip, 'port': port})
        except IndexError:
            pass
        return ret


if __name__ == '__main__':
    t = GetContext()
    print(t.do_collect())
