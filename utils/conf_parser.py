#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import ConfigParser
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF_DIR = os.path.join(BASE_DIR, 'conf')
CONF = os.path.join(CONF_DIR, 'config.ini')
cf = ConfigParser.ConfigParser()
cf.read(CONF)
# global
VERBOSE = cf.getboolean('GLOBAL', 'verbose')
THREAD_COUNT = cf.getint('GLOBAL', 'thread_count')
TIMEOUT = cf.getint('GLOBAL', 'timeout')
# redis
REDIS_HOST = cf.get('REDIS', 'host')
REDIS_PORT = cf.getint('REDIS', 'port')
REDIS_PASSWORD = cf.get('REDIS', 'password')
REDIS_DB = cf.getint('REDIS', 'db')
REDIS_TIMEOUT = cf.getint('REDIS', 'timeout')
# getter
GETTER_THREAD = cf.getboolean('GETTER', 'thread')
GETTER_THREAD_COUNT = cf.getint('GETTER', 'thread_count')
GETTER_CLASSES = [item.strip() for item in cf.get('GETTER', 'classes').split(',') if len(item.strip()) > 0]
# validity
VALIDITY_THREAD = cf.getboolean('VALIDITY', 'thread')
VALIDITY_THREAD_COUNT = cf.getint('VALIDITY', 'thread_count')
VALIDITY_RETRY_COUNT = cf.getint('VALIDITY', 'retry')
VALIDITY_TIMEOUT = cf.getint('VALIDITY', 'timeout')
VALIDITY_URL = cf.get('VALIDITY', 'url')
VALIDITY_POOL_SIZE = cf.get('VALIDITY', 'pool_size')
# schedule
SCHEDULE_VALIDITY = cf.getint('SCHEDULE', 'validity')
SCHEDULE_GETTER = cf.getint('SCHEDULE', 'getter')
# links
LINKS = dict()
for option in cf.options('LINKS'):
    if option == 'verbose':
        continue
    value = [item.strip() for item in cf.get('LINKS', option).split(',')]
    LINKS.update({option: value})
# logging
LOG_PATH = cf.get('LOGGING', 'log_path')
