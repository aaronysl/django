from django.shortcuts import render

# Create your views here.

#  url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from rest_framework_jwt.settings import api_settings

from .models import OAuthQQUser
from.utils import generate_save_user_token


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


# url(r'^qq/user/$', views.QQAuthUserView.as_view()),
class QQAuthUserView(APIView):
    def get(self, request):
        """
        客户端端会发送code参数
        1. 获取code
        2. 获取access_token
        3. 获取openid
        4. 查询 OAuthQQUser 是否有openid=openid的这一条记录
        5. 如果有:
            返回 username,user_id,token
        6. 如果没有:
            返回 access_token ---> 被加密openid
        :param request:
        :return:
        """
        code = request.query_params.get('code', None)
        if not code:
            return Response({'message': '必须提交code'}, status=400)

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        access_token = oauth.get_access_token(code)

        openid = oauth.get_open_id(access_token)

        users = OAuthQQUser.objects.filter(openid=openid)
        # 判断是否绑定了本地用户
        if users:
            # 已经绑定就返回token
            oauth_user = users[0]
            username = oauth_user.user.username
            user_id = oauth_user.user.id
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(oauth_user.user)
            token = jwt_encode_handler(payload)

            return Response({
                'username': username,
                'user_id': user_id,
                'token': token
            })
        else:
            return Response({
                'access_token': generate_save_user_token(openid)  #加密
                # 'access_token': openid  # 加密
            })

    def post(self, request):
        """
        客户端提交的数据
        1. mobile,password,sms_code,access_token

        :param request:
        :return:
        """
        pass