#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
import traceback

from celery.utils.log import get_task_logger

from proxy_get.celery import app
from utils.db.engine import RedisEngine
from utils import conf_parser
from spider.engine.verify import ValidityCheck


logger = get_task_logger(__name__)


def import_class(import_str):
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    try:
        return getattr(sys.modules[mod_str], class_str)
    except AttributeError:
        raise ImportError('Class {} cannot be found ({})'.format(
            class_str, traceback.format_exception(*sys.exc_info())
        ))


def import_object(import_str, *args, **kwargs):
    return import_class(import_str)(*args, **kwargs)


def import_module(import_str):
    __import__(import_str)
    return sys.modules[import_str]


@app.task
def arousal_getter():
    getter_classes = conf_parser.GETTER_CLASSES
    for getter_class in getter_classes:
        getter_detail_async.apply_async(args=[getter_class])


@app.task
def getter_detail_async(getter_class):
    try:
        getter_class = import_class('spider.engine.getter.{getter_name}.Getter'.format(
            getter_name=getter_class.strip()
        ))
        getter = getter_class()
        getter.do_collect()
    except ImportError:
        return


@app.task
def arousal_validity_check():
    engine = RedisEngine()
    activate_list = engine.get()
    proxies_list = []
    for item in activate_list:
        if proxies_list == conf_parser.VALIDITY_POOL_SIZE:
            validity_check_async.apply_async(args=[proxies_list])
            proxies_list = list()
        proxies_list.append(item)
    validity_check_async.apply_async(args=[proxies_list])


@app.task
def validity_check_async(proxies_list):
    v_c = ValidityCheck(proxies_list)
    v_c.do_check()
