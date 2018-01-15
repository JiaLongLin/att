#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import urllib2
import logging
import socket
import httplib

from utils import conf_parser


def makeup_opener(ip, port):
    proxies = {
        'http': '{ip}:{port}'.format(ip=ip, port=port),
        'https': '{ip}:{port}'.format(ip=ip, port=port)
    }
    proxy_header = urllib2.ProxyHandler(proxies)
    opener = urllib2.build_opener(proxy_header)
    return opener


def is_valid(ip, port, retry=None):
    if not retry:
        retry = 0
    opener = makeup_opener(ip, port)
    try:
        opener.open(
            conf_parser.VALIDITY_URL,
            timeout=conf_parser.VALIDITY_TIMEOUT
        )
        return True
    except (
            urllib2.HTTPError,
            urllib2.URLError,
            socket.timeout,
            httplib.BadStatusLine,
            httplib.BAD_REQUEST,
            httplib.NotConnected,
            httplib.FORBIDDEN,
            httplib.HTTPException,
            IOError
    ) as err:
        logging.debug('retry {current} of {count} {ip} {port} invalid. detail: {err}'.format(
            ip=ip,
            port=port,
            err=err,
            count=conf_parser.VALIDITY_RETRY_COUNT,
            current=retry
        ))
        if retry < conf_parser.VALIDITY_RETRY_COUNT:
            retry += 1
            is_valid(ip, port, retry=retry)
        return False
    finally:
        opener.close()
