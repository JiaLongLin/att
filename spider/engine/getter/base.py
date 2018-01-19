#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import absolute_import
import os
import logging
import threading
import time
import urllib
import urlparse

import bs4
import requests
from spider.engine.utils import is_valid

from utils import conf_parser, log
from utils import makeup_header
from utils.db.engine import RedisEngine

if conf_parser.VERBOSE:
    level = 'DEBUG'
else:
    level = 'INFO'

log_file = os.path.join(conf_parser.LOG_PATH, 'getter.log')
log.init_log(log_path=log_file, level=level)


class GetterBase(object):
    """
    Getter Base Class
    """

    get_start_url = lambda url: urllib.splitquery(url)
    # parser_params = lambda href: urlparse.parse_qsl(href)
    url_join = lambda base_url, param: urlparse.urljoin(base_url, param)

    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(makeup_header())
        self.thread = conf_parser.GETTER_THREAD
        self.thread_count = conf_parser.GETTER_THREAD_COUNT
        self.db_engine = RedisEngine()
        self.links_base = conf_parser.LINKS
        self.proxies = None     # :type dict | None
        self.proxy = None   # :type dict | None

    def __del__(self):
        self.session.close()
        if self.proxy:
            self.db_engine.unlock(**self.proxy)

    @property
    def get_proxy(self):
        proxy = self.db_engine.get(single=True)
        self.proxy = {
            'ip': proxy.get('ip'),
            'port': proxy.get('port')
        }
        if not proxy:
            return None
        proxies = {
            "http": "http://%(ip)s:%(port)s" % proxy,
            "https": "http://%(ip)s:%(port)s" % proxy,
        }
        return proxies

    def get_content(self, url, params=None, proxies=None, retry=None, timeout=5):
        """
        get url content
        :param url: url link
        :param params: request params
        :param proxies: proxy setting
        :param retry: retry count
        :param timeout: timeout sec
        :type url: str
        :type params: list[str] | None
        :type proxies: dict | None
        :type retry: int | None
        :type timeout: int
        :return: html code | ''
        """
        if not retry:
            retry = 0
        try:
            if not params:
                if not proxies:
                    req = self.session.get(url, timeout=timeout)
                else:
                    req = self.session.get(url, proxies=proxies, timeout=timeout)
            else:
                if not proxies:
                    req = self.session.get(url, params=params, timeout=timeout)
                else:
                    req = self.session.get(url, params=params, proxies=proxies, timeout=timeout)
        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.HTTPError
        ) as err:
            if self.proxy:
                self.db_engine.unlock(**self.proxy)     # release
            logging.error('{url} connect error. detail: {err}'.format(
                url=url, err=err
            ))
            return ''
        if not req.ok:
            if retry < 3:
                proxies = self.get_proxy
                retry += 1
                time.sleep(0.5)
                self.get_content(url, params, proxies=proxies, retry=retry)
        return req.content

    # @staticmethod
    # def get_start_url(url):
    #     """
    #     split query and path
    #     :param url: url
    #     :return: path
    #     :type url: str
    #     """
    #     return urllib.splitquery(url)[0]

    # @staticmethod
    # def parser_params(href):
    #     """
    #     parse url
    #     :param href: url
    #     :type href: str
    #     :return: dict
    #     """
    #     return dict(urlparse.parse_qsl(href))

    @staticmethod
    def makeup_soup(content):
        """
        :param content: html code
        :type content: str
        :return:
        """
        try:
            soup = bs4.BeautifulSoup(content, 'html.parser')
        except TypeError:
            return None
        return soup

    # @staticmethod
    # def url_join(base_url, param):
    #     return urlparse.urljoin(base_url, param)

    def get_list_nav(self, context, div_id):
        soup = bs4.BeautifulSoup(context, 'html.parser')
        _div = soup.find('div', id=div_id)
        for link in _div.findAll('a'):
            href = link.get('href')
            yield urlparse.parse_qsl(href[1:])

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
            content = self.get_content(**param)
            soup = self.makeup_soup(content)
            self.parser(soup)
        return

    def is_valid(self, ip, port):
        if is_valid(ip, port):
            self.db_engine.append(**{'ip': ip, 'port': port})


class GetterDetailBase(GetterBase, threading.Thread):
    def __init__(self, **kwargs):
        self.link = kwargs.get('link')
        self.params = kwargs.get('params')
        super(GetterDetailBase, self).__init__()

    def parser(self, *args, **kwargs):
        pass

    def run(self):
        content = self.get_content(self.link, params=self.params)
        soup = self.makeup_soup(content)
        self.parser(soup)
