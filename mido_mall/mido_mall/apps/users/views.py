from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView,RetrieveAPIView

from .models import User
from . import serializers
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
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def put(self,request):
        user=self.get_object()
        email=request.data.get('email','')
        user.email=email
        user.save()
        #给邮箱发送邮件
        from django.core.mail import send_mail
        from django.conf import settings

        token='test_token'    #加密的数据
        subject='MIDO_MALL 邮箱验证'
        message=''
        from_email=settings.EMAIL_FROM
        recipient_list=[email]
        html_message='''
        尊敬的用户你好！</br>
        感谢你使用MIDO_MALL</br>
        你的邮箱为%s,请点击链接激活你的邮箱.</br>
        <a href='http://www.meiduo.site:8080/success_verify_email.html?token=%s' >http://www.meiduo.site:8080/success_verify_email.html?token=%s</a>
        
        '''% (email,token,token)

        send_mail(subject,message,from_email,recipient_list,html_message=html_message)

        return Response({'message':'OK'})

