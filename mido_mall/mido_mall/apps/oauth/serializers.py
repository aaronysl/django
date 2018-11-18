import re

from rest_framework import serializers
from django_redis import get_redis_connection
from .utils import check_save_user_token
from users.models import User
from .models import OAuthQQUser

class QQAuthUserSerializer(serializers.Serializer):
    password=serializers.CharField(label='密码',write_only=True,min_length=8,max_length=20)
    mobile=serializers.CharField(label='手机号码',write_only=True,)
    sms_code=serializers.CharField(label='验证码',write_only=True)
    access_token=serializers.CharField(label='openid',write_only=True)

    #校验数据
    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$',value):
            raise serializers.ValidationError('手机号码格式不正确')

        return value

    def validate(self, attrs):
        #sms_code
        #access_token
        #判断用户是否存在

        mobile = attrs['mobile']
        redis_conn = get_redis_connection('verifications')

        real_sms_code = redis_conn.get('sms_%s' % mobile)  # bytes
        if not real_sms_code:
            raise serializers.ValidationError('验证码无效')

        sms_code = attrs['sms_code']
        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('验证码无效')

        access_token=attrs['access_token']
        openid=check_save_user_token(access_token)

        if not openid:
            raise serializers.ValidationError('access token 无效')

        try:
            #如果用户存在，校验密码是否与之匹配
            user=User.objects.get(mobile=mobile)
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码不正确')
        except Exception:
            #如果用户存在，新建用户
            user=User()
            user.username=mobile
            # user.password=attrs['password']   保存的密码为明文
            user.set_password(attrs['password'])
            user.save()
        attrs['openid']=openid
        attrs['user']=user
        return attrs

    def create(self, validated_data):
        user=validated_data['user']
        openid=validated_data['openid']

        oauth_user = OAuthQQUser()
        oauth_user.user=user
        oauth_user.openid = openid
        oauth_user.save()
        return oauth_user



