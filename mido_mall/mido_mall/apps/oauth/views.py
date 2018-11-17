from django.shortcuts import render

# Create your views here.

#  url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
class QQAuthURLView(APIView):

    def get(self,request):

        '''
        1.获取next参数
        2。创建oauth对象
        3。生成login_url
        4。返回login_url
        :param request:
        :return:
        '''

        next=request.query_params.get('next','/')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        login_url=oauth.get_qq_url()
        return Response({
            "login_url":login_url
        })