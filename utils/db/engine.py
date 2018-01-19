#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import time
import json
import logging
# from random import choice, sample

import redis

from utils import conf_parser, log


if conf_parser.VERBOSE:
    level = 'DEBUG'
else:
    level = 'INFO'

log_file = os.path.join(conf_parser.LOG_PATH, 'db_engine.log')
log.init_log(log_path=log_file, level=level)


class RedisEngine(object):
    def __init__(self):
        self.host = conf_parser.REDIS_HOST
        self.port = conf_parser.REDIS_PORT
        self.db = conf_parser.REDIS_DB
        self.password = conf_parser.REDIS_PASSWORD
        self.client = self._connect()
        self.activate_key = 'Proxy:Activate'
        self.proxy_key = '{ip}:{port}'
        self.exists = lambda key: self.client.exists(key)

    def _connect_pool(self):
        pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
        )
        return pool

    def _connect(self):
        try:
            client = redis.StrictRedis(connection_pool=self._connect_pool(), encoding='utf-8')
            return client
        except (
            redis.exceptions.RedisError
        ) as err:
            logging.error(err)
        raise redis.exceptions.RedisError

    # def exists(self, key):
    #     return self.client.exists(key)

    def append(self, ip, port):
        timestamp = int(time.time())
        key = self.proxy_key.format(ip=ip, port=port)
        if self.exists(key):
            return True
        logging.debug('add valid {} proxy to db.'.format(key))
        # pipeline = self.client.pipeline()
        # pipeline.hmset(key, {
        #     'add_time': timestamp,
        #     'ip': ip,
        #     'port': port,
        #     'inUse': False
        # })
        # pipeline.lpush(self.activate_key, key)
        # state = pipeline.execute()
        self.client.sadd(self.activate_key, key)
        state = self.client.hmset(key, {
            'add_time': timestamp,
            'ip': ip,
            'port': port,
            'inUse': False
        })
        logging.debug('add valid {} proxy to db result: {}.'.format(key, json.dumps(state)))
        return state

    def get(self, single=None):
        get_all_lua = """
        redis.call('select', 15)
        local activateKey = KEYS[1]
        local allList = redis.call('smembers', activateKey)
        local proxyList = {}

        local iterateToJson = function (Detail)
            local Tmp = {}
            for key, val in pairs(Detail) do
                if key%2 == 0 then
                    Tmp[Detail[key-1]] = val
                end
            end
            return Tmp
        end

        for key, val in pairs(allList) do
            local proxyDetail = redis.call('hgetall', val)
            table.insert(proxyList, iterateToJson(proxyDetail))
        end
        return cjson.encode(proxyList)
        """
        get_single_lua = """
        redis.call('select', 15)
        local activateKey = KEYS[1]
        local allList = redis.call('smembers', activateKey)
        local iterateToJson = function (Detail)
            local Tmp = {}
            for key, val in pairs(Detail) do
                if key%2 == 0 then
                    Tmp[Detail[key-1]] = val
                end
            end
            return Tmp
        end
        for key, val in pairs(allList) do
            local inUse = redis.call('hget', val, 'inUse')
            if string.lower(inUse) == 'false' then
                local proxyDetail = redis.call('hgetall', val)
                proxyDetail['inUse'] = false
                local _json = iterateToJson(proxyDetail)
                return val
            end
        end
        """
        if not self.client:
            return None
        if not single:
            script = self.client.register_script(get_all_lua)
            ret = script(keys=[self.activate_key], args=[None])
            _ret = []
            for item in json.loads(ret):
                # logging.debug('{}'.format(json.dumps(item)))
                item.update(inUse=eval(item.get('inUse')))
                _ret.append(item)
            return _ret
        script = self.client.register_script(get_single_lua)
        key = script(keys=[self.activate_key], args=[None])
        if not key:
            return None
        proxy = self.client.hgetall(key)
        self.update(key=key, inUse=True)
        return proxy

    def lock(self, ip=None, port=None, key=None):
        if not all(locals()):
            raise ValueError
        if not key:
            key = self.proxy_key.format(ip=ip, port=port)
        logging.debug('lock: {}'.format(key))
        return self.update(key=key, inUse=True)

    def unlock(self, ip=None, port=None, key=None):
        if not all(locals()):
            raise ValueError
        if not key:
            key = self.proxy_key.format(ip=ip, port=port)
        logging.debug('unlock: {}'.format(key))
        return self.update(key=key, inUse=False)

    def remove(self, ip, port):
        # pipeline = self.client.pipeline()
        proxy_key = self.proxy_key.format(ip=ip, port=port)
        logging.debug('remove invalid proxy: {}:{}'.format(ip, port))
        logging.debug('remove invalid proxy {}:{} from activate list.'.format(ip, port))
        # self.client.lrem(self.activate_key, 0, proxy_key)
        self.client.srem(self.activate_key, proxy_key)
        logging.debug('remove invalid proxy {}:{} from db.'.format(ip, port))
        self.client.expire(proxy_key, 0)
        # state = pipeline.execute()
        state = proxy_key not in self.client.lrange(self.activate_key, 0, -1)
        logging.debug('remove action result: {}'.format(json.dumps(state)))
        return state

    def update(self, ip=None, port=None, key=None, **kwargs):
        timestamp = int(time.time())
        if key:
            proxy_key = key
        else:
            proxy_key = self.proxy_key.format(ip=ip, port=port)
        logging.debug('update {} state.'.format(proxy_key))
        pipeline = self.client.pipeline()
        for key, val in kwargs.items():
            logging.debug('{} change key: {} val: {}'.format(proxy_key, key, val))
            pipeline.hset(proxy_key, key, val)
        pipeline.hset(proxy_key, 'updateAt', timestamp)
        logging.debug('{} change key: updateAt val: {}'.format(proxy_key, timestamp))
        state = pipeline.execute()
        logging.debug('update action result: {}'.format(json.dumps(state)))
        return state

    def cleanup(self):
        self.client.flushdb()
