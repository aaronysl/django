from django.shortcuts import render

# Create your views here.

from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, GenericViewSet
from rest_framework_extensions.cache.decorators import cache_response   #缓存使用
from rest_framework_extensions.mixins import CacheResponseMixin
from . import serializers
from .models import Area


# Create your views here.

# 获取省份列表
# url(r'^areas/$',AreaApiView.as_view({'get':'list'}))

# 获取下一级地区列表
# url(r'^areas/(?P<pk>\d+)/$',AreaApiView.as_view({'get':'retrieve'}))

class AreaApiView(ViewSet):
    @cache_response(timeout=60, cache='default')
    def list(self, request):
        # 获取所有省份
        # 序列化输出
        provinces = Area.objects.filter(parent=None)
        pses = serializers.AreaSerializer(provinces, many=True)
        return Response(pses.data)

    @cache_response(timeout=60, cache='default')
    def retrieve(self, request, pk):
        # 获取当前地区对象
        areas_obj = Area.objects.get(pk=pk)
        # 序列化输出
        serializer = serializers.AreaSubsSerializer(areas_obj)

        return Response(serializer.data)
