from celery import Celery

# 为celery使用django配置文件进行设置
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mido_mall.settings.dev'
    import django
    django.setup()  #初始化Django 链接服务器

# 创建celery应用ls
app = Celery('mido')

# 导入celery配置
app.config_from_object('celery_tasks.config')

# 自动注册celery任务
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.send_mails'])

