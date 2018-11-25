from django.shortcuts import render
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
# Create your views here.

from .models import SKU

from .serializers import SkuSerializer


# url(r'^/categories/(?P<category_id>\d+)/skus/$',SkuApiView.as_view())
class SkuApiView(ListAPIView):
    serializer_class = SkuSerializer
    # 按照字段排序
    filter_backends = (OrderingFilter,)
    ordering_fields = ('create_time', 'price', 'sales')

    def get_queryset(self):
        return SKU.objects.filter(is_launched=True, category_id=self.kwargs['category_id'])

    # def get(self,request,category_id):
    #     # 1. 查询商品数据 category_id is_launched
    #     # 2. 分页
    #     # 3. 构建序列化器
    #     # 4. 序列化返回
    #     pass
