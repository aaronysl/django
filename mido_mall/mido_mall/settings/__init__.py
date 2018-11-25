from django.db.models.signals import post_delete, post_save


# 定义接受信号者
def static_list(sender, **kwargs):
    print(sender)
    print(kwargs)
    # 1. 判断sender是否是GoodsCategory
    # 2. 发送生成list静态的任务给celery
    if getattr(sender, '__name__', 'none') == 'GoodsCategory':
        from celery_tasks.htmls.tasks import generate_static_list_search_html
        generate_static_list_search_html.delay()


# 商品静态化
def create_sku_html(sender, **kwargs):
    # 判断是否更新的是商品 SKU,SKUImage,SKUSpecification,SpecificationOption,GoodsSpecification
    # 如果是就更新页面
    # kwargs:
    # signal
    # instance 修改或新建的模型类对象

    if getattr(sender, '__name__', 'none') == 'SKU':
        from celery_tasks.htmls.tasks import generate_static_sku_detail_html
        instance = kwargs['instance']
        generate_static_sku_detail_html.delay(instance.id)


# 绑定信号
post_save.connect(static_list)
post_delete.connect(static_list)

post_save.connect(create_sku_html)
