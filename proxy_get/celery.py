#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

from celery import Celery, platforms
from celery.schedules import crontab
from kombu import Queue, Exchange
from django import setup

from utils import conf_parser as parser, log

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'att.settings')
setup()

log_file = os.path.join(parser.LOG_PATH, 'getter.log')
if not os.path.exists(parser.LOG_PATH):
    os.mkdir(parser.LOG_PATH)

if parser.VERBOSE:
    level = 'DEBUG'
else:
    level = 'INFO'

log.init_log(log_path=log_file, level=level)

prefix = 'proxy'
app_name = '{}_get'.format(prefix)
platforms.C_FORCE_ROOT = True       # 解决celery不能在root下运行的问题

CELERY_QUEUES = (
    Queue(
        '{}_getter'.format(prefix),
        Exchange('{}_getter'.format(prefix)),
        routing_key='{}_getter_key'.format(prefix)
    ),
    Queue(
        '{}_detail'.format(prefix),
        Exchange('{}_detail'.format(prefix)),
        routing_key='{}_detail_key'.format(prefix)
    ),
    Queue(
        '{}_validity'.format(prefix),
        Exchange('{}_validity'.format(prefix)),
        routing_key='{}_validity_check_key'.format(prefix)
    ),
)

CELERY_ROUTES = {
    '{}.tasks.arousal_getter'.format(app_name): {
        'queue': '{}_getter'.format(prefix),
        'routing_key': '{}_getter_key'.format(prefix)
    },
    '{}.tasks.getter_detail_async'.format(app_name): {
        'queue': '{}_detail'.format(prefix),
        'routing_key': '{}_detail_key'.format(prefix)
    },
    '{}.tasks.arousal_validity_check'.format(app_name): {
        'queue': '{}_validity'.format(prefix),
        'routing_key': '{}_validity_check_key'.format(prefix)
    },
    '{}.tasks.validity_check_async'.format(app_name): {
        'queue': '{}_validity'.format(prefix),
        'routing_key': '{}_validity_check_key'.format(prefix)
    },
}

BROKER_URL = 'redis://:{}@{}:{}/3'.format(
    parser.REDIS_PASSWORD,
    parser.REDIS_HOST,
    parser.REDIS_PORT
)

BACKEND_URL = 'redis://:{}@{}:{}/7'.format(
    parser.REDIS_PASSWORD,
    parser.REDIS_HOST,
    parser.REDIS_PORT
)

app = Celery(
    app_name,
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=['{}.tasks'.format(app_name)]
)

app.conf.update(
    CELERY_TASK_RESULTS=60,
    CELERY_ENABLE_UTF=False,
    CELERY_TIMEZONE='Asia/Shanghai',
    CELERY_ACCEPT_CONTENT=['json', 'pickle', 'msgpack', 'yaml'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERYBEAT_SCHEDULE={},
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_QUEUES=CELERY_QUEUES,
    CELERY_ROUTES=CELERY_ROUTES
)

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'add-every-{}-minutes-getter'.format(parser.SCHEDULE_GETTER): {
            'task': '{}.tasks.arousal_getter'.format(app_name),
            'schedule': crontab(
                minute='*/{}'.format(parser.SCHEDULE_GETTER),
                app=app_name
            )
        },
        'add-every-{}-minutes-arousal_validity_check'.format(
            parser.SCHEDULE_VALIDITY): {
            'task': '{}.tasks.arousal_validity_check'.format(app_name),
            'schedule': crontab(
                minute='*/{}'.format(parser.SCHEDULE_VALIDITY),
                app=app_name
            )
        },
    }
)


if __name__ == '__main__':
    app.start()
