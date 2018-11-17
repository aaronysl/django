import random


from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from celery_tasks.sms.tasks import send_sms_code

# Create your views here.
# url('^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),


class SMSCodeView(APIView):
    def get(self, request, mobile):
        '''
        1. 校验短信是否发送过
        2. 如果已发送,返回已发送消息
        3. 生成随机验证码
        4. 保存验证码到redis中 sms_{mobile}
        5. 保存已发送状态 smsflag_{mobile}
        6. 给用户手机发短信
        7. 返回客户端发送成功
        :param request:
        :param mobile:
        :return:
        '''
        # print('111')
        redis_conn=get_redis_connection('verifications')

        send_flag=redis_conn.get('smsflag_%s'% mobile)

        if send_flag:
            return Response({'message':'短信发送频繁'},status=400)

        sms_code=random.randint(10000,99999)


        #保存验证码
        # redis_conn.setex('sms_%s' % mobile, 3*60, sms_code)
        #保存发送状态
        # redis_conn.setex('smsflag%s' % mobile, 60 ,1)
        # print('222')
        #获取管道对象
        pipeline=redis_conn.pipeline()
        #往管道添加命令
        pipeline.setex('sms_%s' % mobile, 3*60, sms_code)
        pipeline.setex('smsflag%s' % mobile, 60 ,1)
        #执行管道中所有命令
        pipeline.execute()

        #发送短信给用户手机
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],
        #                         constants.SEND_SMS_TEMPLATE_ID)
        # 依赖于网络情况,

        send_sms_code.delay(mobile,sms_code,5)
        # 发布任务,立即返回


        return Response({'message':'OK'})


