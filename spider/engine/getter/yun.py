#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import threading

import bs4

from spider.engine.getter.base import GetterBase


class GetterDetail(threading.Thread):
    def __init__(self, url, params=None):
        super(GetterDetail, self).__init__()
        self.link = url
        self.params = params
        self.getter = Getter()

    def run(self):
        content = self.getter.get_content(self.link, self.params)
        self.getter.parser(content)


class Getter(GetterBase):
    def __init__(self):
        super(Getter, self).__init__()
        self.links = self.links_base.get('yun')

    def parser(self, context):
        soup = bs4.BeautifulSoup(context, 'html.parser')
        _list_div = soup.find('div', id='list')
        trs = _list_div.find('table').findAll('tr')
        try:
            for tr in trs[1:]:
                tds = tr.findAll('td')
                ip = tds[0].get_text()
                port = tds[1].get_text()
                self.is_valid(ip, port)
        except IndexError:
            pass

    def do_collect(self):
        params = []
        for url in self.links:
            start_url = self.get_start_url(url)
            context = self.get_content(url)
            list_nav = self.get_list_nav(context, 'listnav')
            while True:
                try:
                    param = list_nav.next()
                except StopIteration:
                    break
                params.append({'url': start_url, 'params': param})
        self._call(params)

    def call_threading(self, *args, **kwargs):
        getter = GetterDetail(**kwargs)
        getter.start()
