from celery_tasks.main import app
from django.core.mail import send_mail
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as TS


@app.task(name='send_email')
def send_email(user_id,email):
    # 给邮箱发送邮件
    ts = TS(settings.SECRET_KEY, expires_in=60 * 60 * 1)  # 邮箱验证过期时间1小时
    data = {
        'user_id': user_id,
        'email': email
    }
    token = ts.dumps(data).decode()
    # token='test_token'    #加密的数据
    subject = 'MIDO_MALL 邮箱验证'
    message = ''
    from_email = settings.EMAIL_FROM
    recipient_list = [email]
    html_message = '''
            尊敬的用户你好！</br>
            感谢你使用MIDO_MALL</br>
            你的邮箱为%s,请点击链接激活你的邮箱.</br>
            <a href='http://www.meiduo.site:8080/success_verify_email.html?token=%s' >http://www.meiduo.site:8080/success_verify_email.html?token=%s</a>

            ''' % (email, token, token)

    send_mail(subject, message, from_email, recipient_list, html_message=html_message)

