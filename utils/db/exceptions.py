#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from redis.exceptions import RedisError


class RedisEngineError(RedisError):
    pass
