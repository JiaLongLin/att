#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import threading
from lxml import etree

from spider.engine.getter.base import GetterBase


class Getter(GetterBase):
    def __init__(self):
        super(Getter, self).__init__()
        self.links = self.links_base.get('guobanjia')

    def do_collect(self):
        params = []
        for link in self.links:
            # start_url = self.get_start_url(link)
            content = self.get_content(url=link)
            soup = self.makeup_soup(content)
            list_nav = self.get_list_nav(soup, class_name='wp-pagenavi')
            while True:
                try:
                    param = list_nav.next()
                except StopIteration:
                    break
                params.append({'url': 'http://www.goubanjia.com/free/'+param})
        self._call(params)

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
            self.parser(content)
        return

    @staticmethod
    def etree_parser(content):
        # type: (content) -> etree
        return etree.HTML(content)

    def parser(self, content):
        tree = self.etree_parser(content)
        if not tree:    # tree is None
            return
        xpath_str = """
        .//*[not(contains(@style, 'display: none'))
        and not(contains(@style, 'display:none'))
        and not(contains(@class, 'port'))
        ]/text()
        """
        try:
            proxy_list = tree.xpath('//td[@class="ip"]')
            for each_proxy in proxy_list:
                try:
                    ip = ''.join(each_proxy.xpath(xpath_str))
                    port = each_proxy.xpath(".//span[contains(@class, 'port')]/text()")[0]
                    self.is_valid(ip, port)
                except Exception as err:
                    logging.error(err)
        except AttributeError:
            return


    def call_threading(self, *args, **kwargs):
        getter = GetterDetail(**kwargs)
        getter.start()

    def get_list_nav(self, soup, class_name):
        _div = soup.find('div', {'class': class_name})
        try:
            last_page = _div.findAll('a')[-1]
            last_number = last_page.get_text()
            for item in range(1, int(last_number)+1):
                yield 'index{}.shtml'.format(item)
        except (AttributeError, IndexError):
            return


class GetterDetail(threading.Thread):
    def __init__(self, url, params=None):
        super(GetterDetail, self).__init__()
        self.link = url
        self.params = params
        self.getter = Getter()

    def run(self):
        content = self.getter.get_content(self.link, self.params)
        self.getter.parser(content)
