#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from spider.engine.getter.base import GetterBase


class Getter(GetterBase):
    def __init__(self):
        super(Getter, self).__init__()
        self.links = self.links_base.get('ip181')

    def do_collect(self):
        for link in self.links:
            content = self.get_context(link)
            soup = self.makeup_soup(content)
            tbody = soup.find('tbody')
            try:
                trs = tbody.findAll('tr')[1:]
                for tr in trs:
                    tds = tr.findAll('td')
                    ip = tds[0].get_text()
                    port = tds[1].get_text()
                    self.is_valid(ip, port)
            except IndexError:
                pass
