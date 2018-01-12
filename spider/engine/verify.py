#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import threading

from spider.engine.utils import is_valid
from utils import conf_parser
from utils.db.engine import RedisEngine


class VerifyProxyValidity(threading.Thread):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.db_engine = RedisEngine()
        super(VerifyProxyValidity, self).__init__()

    def run(self):
        if is_valid(self.ip, self.port):
            self.db_engine.update(ip=self.ip, port=self.port)
        else:
            self.db_engine.remove(ip=self.ip, port=self.port)


class ValidityCheck(object):
    def __init__(self, proxies_list):
        self.db_engine = RedisEngine()
        self.proxies_list = proxies_list
        self.thread = conf_parser.VALIDITY_THREAD
        self.thread_count = conf_parser.VALIDITY_THREAD_COUNT

    def _check(self, ip, port):
        if is_valid(ip, port):
            self.db_engine.update(ip=ip, port=port)
        else:
            self.db_engine.remove(ip=ip, port=port)

    def do_check(self):
        if self.thread:
            index = 0
            while index < len(self.proxies_list):
                if threading.activeCount() < self.thread_count:
                    proxies = self.proxies_list[index]
                    thread = VerifyProxyValidity(
                        ip=proxies.get('ip'),
                        port=proxies.get('port')
                    )
                    thread.start()
                    index += 1
            return
        for proxies in self.proxies_list:
            self._check(
                ip=proxies.get('ip'),
                port=proxies.get('port')
            )
