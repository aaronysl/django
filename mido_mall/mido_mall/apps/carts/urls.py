from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^cart/$', views.UserCartView.as_view())
]
