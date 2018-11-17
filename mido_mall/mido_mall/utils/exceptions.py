import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from django.db import DatabaseError
from redis.exceptions import RedisError

# 获取django日志器
logger = logging.getLogger('django')


def exception_handler(exc, context):
    """

    :param exc: 异常对象
    :param context: 异常上下文
    :return:
    """
    # 1. drf处理异常
    # 2. 自己处理异常
    response = drf_exception_handler(exc, context)

    # drf 是否处理完成
    if not response:
        # 自己处理
        logging.error('[%s] %s' % (context['view'], exc))
        if isinstance(exc, DatabaseError) or isinstance(exc, RedisError):
            return Response({'error': "服务内部异常"}, status=507)  # 507代表数据库异常

    return response
