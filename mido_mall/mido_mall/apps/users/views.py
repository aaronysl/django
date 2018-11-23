from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView,RetrieveAPIView,UpdateAPIView

from .models import User
from . import serializers
from celery_tasks.send_mails.tasks import send_email
# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),


class UsernameCountView(APIView):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        data = {
            "username": username,
            "count": count
        }
        return Response(data)



# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class MobileCountView(APIView):
    """
    手机号数量
    """
    def get(self, request, mobile):
        """
        获取指定手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)



# url(r'^users/$', views.UserView.as_view()),
class UserView(CreateAPIView):
    serializer_class = serializers.CreateUserSerializer


#手动实现登录接口，可扩展性较差
class LoginApiView(APIView):
    def post(self,request):
        data=request.data
        username=data.get('username','')
        password=data.get('password','')

        users =User.objects.filter(Q(username=username) | Q(mobile=username))       #queryset要么有一个元素，要么没有元素
        if users:
            #用户存在
            user=users[0]
            #校验密码
            if user.check_password(password):
                #颁发token
                # 生成jwt token
                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)

                return Response({
                    'username':user.username,
                    'user_id':user.id,
                    'token':token
                })
            return Response({'message':'用户名或密码错误'},status=400)


#GET /User/
#url(r'user/',UserDetailView.as_view())
class UserDetailView(RetrieveAPIView):
    """
        用户详情
    """
    serializer_class = serializers.UserDetailSerializer
    permission_classes =(IsAuthenticated,)

    def get_object(self):
        return self.request.user

    # def get(self,request,pk):
    #
    #     user=self.get_object()
    #
    #     us=self.get_serializer(user)
    #
    #     return Response(data=us.data)


# PUT /email/
# url(r'^email/$',UserEmailApi.as_view())
class UserEmailApi(GenericAPIView):
    # serializer_class = serializers.UserEmailSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def put(self,request):

        user=self.get_object()
        email=request.data.get('email','')
        user.email=email
        user.save()
        #给邮箱发送邮件
        #是有celery发送邮件
        #----
        send_email.delay(user_id=user.id,email=user.email)
        #---
        # token=user.create_email_token()
        # send_email.delay(email,token)

        return Response({'message':'OK'})


# GET/PUT  emails/verification/?token=token
# url(r'^emails/verification/$',EmailVerifyApi.as_view())
class EmailVerifyApi(APIView):
    def get(self,request):

        token=request.query_params.get('token',False)
        if not token:
            return Response({'message': "必须传递token"}, status=400)

        #解析token
        from django.conf import settings
        from itsdangerous import TimedJSONWebSignatureSerializer as TS

        ts = TS(settings.SECRET_KEY, expires_in=60 * 60 * 1)  # 邮箱验证过期时间1小时

        try:
            data=ts.loads(token)
        except Exception:
            return Response({'message':'token无效'},status=400)
        #查询需要激活的用户
        user_id=data['user_id']
        email=data['email']

        try:
            user=User.objects.get(id=user_id,email=email)
        except Exception:
            return Response({'message': 'token无效'}, status=400)
        #激活邮箱
        user.email_active=True
        user.save()

        return Response({'message':'OK'})




