from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from goods.models import SKU
from . import serializers


# Create your views here.

# '/ orders / settlement'
class OrdersSettlementView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        # 获取商品id和数量
        user = request.user
        conn = get_redis_connection('cart')

        cart_id = 'cart_%d' % user.id
        cart_selected_id = 'cart_selected_%d' % user.id
        # {
        #     sku_id:count
        #     b'1':b'10'
        # }
        sku_ids = conn.hgetall(cart_id)
        # {b'1',b'2'}
        cart_selected_ids = conn.smembers(cart_selected_id)
        # 查询数据
        skus = []
        for sku_id in cart_selected_ids:
            sku = SKU.objects.get(id=int(sku_id))
            sku.count = int(sku_ids[sku_id])
            skus.append(sku)
        data = dict()
        data['freight'] = 10
        data['skus'] = serializers.OrderSkuSerializer(skus, many=True).data

        return Response(data)


#  POST /orders/
class OrderCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)

    serializer_class = serializers.OrderCreateSerializer
