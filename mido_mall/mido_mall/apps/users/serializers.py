import re

from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .models import User


class CreateUserSerializer(serializers.ModelSerializer):

    '''
    提交字段
    1. username
    2. password
    3. password2
    4. mobile
    5. sms_code
    6. allow
    返回字段
    1. id
    2. username
    3. mobile
    4. jwt token
    '''
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    # 'true'
    allow = serializers.CharField(label='是否同意协议', write_only=True)

    token = serializers.CharField(label='token', read_only=True)

    class Meta:
        model=User
        fields=['id','username','mobile','password','password2','sms_code','allow','token']

        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 32,
            },
            'username': {
                'min_length': 5,
                'max_length': 20,
            }

        }

    def validate_mobile(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机格式不对')
        return value

    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('请同意协议')
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value):
            raise serializers.ValidationError('用户名已存在')

        return value

    def validate(self, attrs):
        password = attrs['password']
        password2 = attrs['password2']
        if password != password2:
            raise serializers.ValidationError('密码不匹配')

        mobile = attrs['mobile']
        redis_conn = get_redis_connection('verifications')

        real_sms_code = redis_conn.get('sms_%s' % mobile)  # bytes
        if not real_sms_code:
            raise serializers.ValidationError('验证码无效')

        sms_code = attrs['sms_code']
        if sms_code != real_sms_code.decode():
            raise serializers.ValidationError('验证码无效')

        return attrs

    def create(self, validated_data):

        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        user = super().create(validated_data)

        user.set_password(validated_data['password'])
        user.save()

        #生成jwt token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token=token
        return user