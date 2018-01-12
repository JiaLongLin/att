#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import threading
import time
import urllib
import urlparse

import bs4
import requests
from spider.engine.utils import is_valid

from spider.links import LINKS
from utils import conf_parser
from utils import makeup_header
from utils.db.engine import RedisEngine


class GetterBase(object):
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(makeup_header())
        self.thread = conf_parser.GETTER_THREAD
        self.thread_count = conf_parser.GETTER_THREAD_COUNT
        self.db_engine = RedisEngine()
        self.links_base = LINKS
        self.proxies = None

    def __del__(self):
        self.session.close()

    @property
    def get_proxy(self):
        proxy = self.db_engine.get(single=True)
        if not proxy:
            return None
        proxies = {
            "http": "http://%(ip)s:%(port)s" % proxy,
            "https": "http://%(ip)s:%(port)s" % proxy,
        }
        return proxies

    def get_context(self, url, params=None, proxies=None, retry=None):
        if not retry:
            retry = 0
        try:
            if not params:
                if not proxies:
                    req = self.session.get(url)
                else:
                    req = self.session.get(url, proxies=proxies)
            else:
                if not proxies:
                    req = self.session.get(url, params=params)
                else:
                    req = self.session.get(url, params=params, proxies=proxies)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.HTTPError
        ) as err:
            logging.error('{url} connect error. detail: {err}'.format(
                url=url, err=err
            ))
            return ''
        if not req.ok:
            if retry < 3:
                proxies = self.get_proxy
                retry += 1
                time.sleep(0.5)
                self.get_context(url, params, proxies=proxies, retry=retry)
        return req.content

    @staticmethod
    def get_start_url(url):
        return urllib.splitquery(url)[0]

    @staticmethod
    def parser_params(href):
        return dict(urlparse.parse_qsl(href))

    @staticmethod
    def makeup_soup(content):
        try:
            soup = bs4.BeautifulSoup(content, 'html.parser')
        except TypeError:
            return None
        return soup

    @staticmethod
    def url_join(base_url, param):
        return urlparse.urljoin(base_url, param)

    def get_list_nav(self, context, div_id):
        soup = bs4.BeautifulSoup(context, 'html.parser')
        _div = soup.find('div', id=div_id)
        for link in _div.findAll('a'):
            href = link.get('href')
            yield self.parser_params(href[1:])

    def call_threading(self, *args, **kwargs):
        pass

    def parser(self, soup):
        pass

    def _call(self, params):
        if self.thread:
            index = 0
            while index < len(params):
                if threading.activeCount() < self.thread_count:
                    self.call_threading(**params[index])
                    index += 1
            return
        for param in params:
            content = self.get_context(**param)
            soup = self.makeup_soup(content)
            self.parser(soup)
        return

    def is_valid(self, ip, port):
        if is_valid(ip, port):
            self.db_engine.append(**{'ip': ip, 'port': port})


class GetterDetailBase(GetterBase, threading.Thread):
    def __init__(self, *args, **kwargs):
        self.link = kwargs.get('link')
        self.params = kwargs.get('params')
        super(GetterDetailBase, self).__init__()

    def parser(self, *args, **kwargs):
        pass

    def run(self):
        content = self.get_context(self.link, params=self.params)
        soup = self.makeup_soup(content)
        self.parser(soup)
