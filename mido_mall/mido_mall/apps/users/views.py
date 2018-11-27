from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, GenericViewSet
from rest_framework_jwt.settings import api_settings
from django.db.models import Q
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView,RetrieveAPIView,UpdateAPIView
from rest_framework_jwt.views import ObtainJSONWebToken

from .models import User,Address
from . import serializers
from goods.models import SKU
from goods.serializers import SkuSerializer
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


class UserAddressApiView(GenericViewSet):
    permission_classes = (IsAuthenticated,)

    # 获取地址列表
    def list(self, request):
        # 获取当前用户
        user = self.request.user
        # 获取当前用户所有地址
        addresses = user.addresses.filter(is_deleted=False)
        # 序列化输出
        serializer = serializers.UserAddressSerializer(addresses, many=True)
        data = {
            'addresses': serializer.data,
            'limit': 15,
            'default_address_id': user.default_address.id if user.default_address else 0
        }
        return Response(data)

    # 新建
    def create(self, request):
        # 获取提交的数据
        # 构建序列化器对象
        # 校验数据
        # 保存对象
        # 序列化输出
        data = request.data
        serializer = serializers.UserAddressSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data)

    # 更新
    def update(self, request, pk):
        # 获取要更细的地址
        # 获取提交的数据
        # 构建序列化器
        # 校验数据
        # 保存
        # 序列化输出
        address = Address.objects.get(pk=pk)
        data = request.data
        serializer = serializers.UserAddressSerializer(instance=address, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # 删除
    def destroy(self, request, pk):
        # 获取要删除的地址
        # 执行删除
        address = Address.objects.get(pk=pk)
        address.is_deleted = True
        address.save()

        return Response(status=204)

    # 默认地址
    @action(methods=['put'], detail=True)  # addresses/<pk>/status/
    def status(self, request, pk):
        # 获取地址
        # 把当前用户default_address改为获取的地址
        address = Address.objects.get(pk=pk)
        user = self.request.user
        user.default_address = address
        user.save()

        return Response({'message': 'OK'})

    # 更新标题
    @action(methods=['put'], detail=True)  # addresses/<pk>/title/
    def title(self, request, pk):
        # 获取地址
        # 获取title
        # 更新title
        # 序列化输出
        address = Address.objects.get(pk=pk)
        title = request.data.get('title', '')
        address.title = title
        address.save()
        return Response(serializers.UserAddressSerializer(address).data)

class UserHistory(APIView):
    permission_classes = (IsAuthenticated,)     # 用户必须是已登录

    def post(self, request):
        # sku_id
        sku_id = request.data.get('sku_id', 0)
        # 判断是否存在
        try:
            SKU.objects.get(id=sku_id)
        except Exception:
            return Response({'error': "商品不存在"}, status=400)

        user_id = request.user.id

        conn = get_redis_connection('history')
        pipeline = conn.pipeline()

        # 删除指定sku_id
        pipeline.lrem('history_%d' % user_id, 0, sku_id)

        # 添加sku_id
        pipeline.lpush('history_%d' % user_id, sku_id)

        # 只保留5条数据
        pipeline.ltrim('history_%d' % user_id, 0, 5)

        pipeline.execute()

        return Response({'message': 'OK'})

    def get(self, request):
        user_id = request.user.id
        conn = get_redis_connection('history')
        sku_ids = conn.lrange('history_%d' % user_id, 0, 5)

        skus = []
        for sku_id in sku_ids:
            skus.append(SKU.objects.get(id=sku_id))

        serializer = SkuSerializer(skus, many=True)

        return Response(serializer.data)


from datetime import datetime
from carts.utils import merge_cookie_cart_to_redis_cart

jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


class AuthenticateView(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')

            response_data = jwt_response_payload_handler(token, user, request)

            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)

            response = merge_cookie_cart_to_redis_cart(request, user, response)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

