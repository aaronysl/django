import json

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django_redis import get_redis_connection

from goods.models import SKU
from . import serializers


# Create your views here.


class UserCartView(APIView):
    def perform_authentication(self, request):
        pass

    def post(self, request):
        # 获取数据
        data = request.data
        sku_id = data['sku_id']
        count = data['count']
        selected = data.get('selected', False)

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 异常说民用户未登录
            user = None
        if user is not None and user.is_authenticated:
            # 操作redis
            conn = get_redis_connection('cart')
            cart_id = 'cart_%d' % user.id
            cart_selected_id = 'cart_selected_%d' % user.id
            pipeline = conn.pipeline()
            # 修改商品数量
            pipeline.hincrby(cart_id, sku_id, count)

            if selected:
                # 添加选中状态
                pipeline.sadd(cart_selected_id, sku_id)
            else:
                # 移除选中状态
                pipeline.srem(cart_selected_id, sku_id)
            pipeline.execute()
            return Response(data, status=201)
        else:
            # 操作cookie
            cart_cookie = request.COOKIES.get('cart', None)
            if cart_cookie:
                cart = json.loads(cart_cookie)
            else:
                cart = {}

            # 修改购物车数量
            if sku_id in cart:
                cart[sku_id]['count'] += count
            else:
                cart[sku_id] = {
                    "count": count
                }
            # 修改是否选中
            if selected:
                cart[sku_id]['selected'] = True
            else:
                cart[sku_id]['selected'] = False

            response = Response(data, status=201)
            response.set_cookie('cart', json.dumps(cart), max_age=60 * 60 * 24 * 365)

            return response

    def get(self, request):
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 异常说民用户未登录
            user = None
        if user is not None and user.is_authenticated:
            # 获取商品id和数量
            conn = get_redis_connection('cart')
            cart_id = 'cart_%d' % user.id
            cart_selected_id = 'cart_selected_%d' % user.id
            # {
            #     sku_id:count
            #     b'1':b'10'
            # }
            sku_ids = conn.hgetall(cart_id)
            cart_selected_ids = conn.smembers(cart_selected_id)
            skus = []
            for sku_id in sku_ids:
                sku = SKU.objects.get(id=int(sku_id))
                sku.count = int(sku_ids[sku_id])

                if sku_id in cart_selected_ids:
                    sku.selected = True
                else:
                    sku.selected = False

                skus.append(sku)
            serializer = serializers.CartSkuSerializer(skus, many=True)
            return Response(serializer.data)
        else:
            # 操作cookie
            cart_cookie = request.COOKIES.get('cart', None)
            if cart_cookie:
                cart = json.loads(cart_cookie)
            else:
                cart = {}
            # {
            #     sku_id:{
            #         count
            #         selected
            #     }
            # }
            skus = []
            for sku_id in cart:
                sku = SKU.objects.get(id=sku_id)
                sku.count = cart[sku_id]['count']
                sku.selected = cart[sku_id]['selected']
                skus.append(sku)

            serializer = serializers.CartSkuSerializer(skus, many=True)
            return Response(serializer.data)

    def put(self, request):
        data = request.data
        sku_id = data['sku_id']
        count = data['count']
        selected = data.get('selected', False)
        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 异常说民用户未登录
            user = None
        if user is not None and user.is_authenticated:
            conn = get_redis_connection('cart')
            cart_id = 'cart_%d' % user.id
            cart_selected_id = 'cart_selected_%d' % user.id
            pipeline = conn.pipeline()
            # 设置sku_id数量
            pipeline.hmset(cart_id, {sku_id: count})
            # 修改选中状态
            if selected:
                pipeline.sadd(cart_selected_id, sku_id)
            else:
                pipeline.srem(cart_selected_id, sku_id)
            pipeline.execute()

            return Response(data, status=201)

        else:
            # 操作cookie
            cart_cookie = request.COOKIES.get('cart', None)
            if cart_cookie:
                cart = json.loads(cart_cookie)
            else:
                cart = {}

            if selected:
                cart[str(sku_id)] = {
                    "count": count,
                    "selected": True
                }
            else:
                cart[str(sku_id)] = {
                    "count": count,
                    "selected": False
                }
            response = Response(data, status=201)
            response.set_cookie('cart', json.dumps(cart), max_age=60 * 60 * 24 * 365)
            return response

    def delete(self, request):
        data = request.data
        sku_id = data['sku_id']
        try:
            user = request.user
        except Exception:
            # 异常说明用户未登录
            user = None
        if user is not None and user.is_authenticated:
            conn = get_redis_connection('cart')
            cart_id = 'cart_%d' % user.id
            cart_selected_id = 'cart_selected_%d' % user.id
            pipeline = conn.pipeline()
            # 删除商品
            pipeline.hdel(cart_id, sku_id)
            # 移出选中状态
            pipeline.srem(cart_selected_id, sku_id)
            pipeline.execute()
            return Response(status=204)
        else:
            # 操作cookie
            cart_cookie = request.COOKIES.get('cart', None)
            if cart_cookie:
                cart = json.loads(cart_cookie)
            else:
                cart = {}
            if str(sku_id) in cart:
                del cart[str(sku_id)]

            response = Response(status=204)
            response.set_cookie('cart', json.dumps(cart), max_age=60 * 60 * 24 * 365)
            return response