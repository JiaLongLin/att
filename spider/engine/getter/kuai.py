#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import threading

from spider.engine.getter.base import GetterBase


class Getter(GetterBase):
    def __init__(self):
        super(Getter, self).__init__()
        self.links = self.links_base.get('kuai')

    def do_collect(self):
        params = []
        for link in self.links:
            start_url = self.get_start_url(link)
            for item in range(1, 50):
                params.append({'url': '{start_url}{page_num}/'.format(start_url=start_url, page_num=item)})
        self._call(params)

    def parser(self, soup):
        _list_div = soup.find('div', id='list')
        if not _list_div:
            logging.warning('//div[@id="list"] not found.')
            return
        table_body = _list_div.find('tbody')
        trs = table_body.findAll('tr')
        for tr in trs:
            tds = tr.findAll('td')
            ip = tds[0].get_text()
            port = tds[1].get_text()
            self.is_valid(ip, port)

    def call_threading(self, *args, **kwargs):
        getter = GetterDetail(**kwargs)
        getter.start()

    def get_list_nav(self, soup, div_id):
        _div = soup.find('div', id=div_id)
        try:
            for link in _div.findAll('a'):
                href = link.get('href')
                yield href
        except AttributeError:
            return


class GetterDetail(threading.Thread):
    def __init__(self, link, params=None):
        self.link = link
        self.params = params
        self.getter = GetterBase()
        super(GetterDetail, self).__init__()

    def run(self):
        content = self.getter.get_content(self.link, params=self.params)
        soup = self.getter.makeup_soup(content)
        self.getter.parser(soup)
