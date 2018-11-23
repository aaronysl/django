from django.conf.urls import url
from rest_framework.routers import SimpleRouter #自动生成路由

from . import views

urlpatterns = [
    # url(r'^areas/$', views.AreaApiView.as_view({'get': 'list'})),
    # url(r'^areas/(?P<pk>\d+)/$', views.AreaApiView.as_view({'get': 'retrieve'}))
]

router = SimpleRouter()
router.register('areas', views.AreaApiView, base_name='areas')

urlpatterns += router.urls
