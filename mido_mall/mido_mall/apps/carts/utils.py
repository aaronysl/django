import json

from django_redis import get_redis_connection


def merge_cookie_cart_to_redis_cart(request, user, response):
    # 获取cookie_cart
    cookie = request.COOKIES.get('cart', None)
    if not cookie:
        cookie_cart = {}
    else:
        # {
        #     '1':{
        #         "count":10,
        #         "selected":False
        #     }
        # }
        cookie_cart = json.loads(cookie)
    # 修改cookie中key为整数
    cookie_cart_with_int = dict()
    for key, value in cookie_cart.items():
        cookie_cart_with_int[int(key)] = value

    # 获取redis中数据,构建为与cookie同结构字典
    conn = get_redis_connection('cart')
    cart_id = 'cart_%d' % user.id
    cart_selected_id = 'cart_selected_%d' % user.id
    # 获取商品sku_id:count b'1':b'10'
    sku_ids = conn.hgetall(cart_id)
    # b'1'
    selected_ids = conn.smembers(cart_selected_id)

    redis_cart = dict()
    for key, value in sku_ids.items():
        redis_cart[int(key)] = {
            "count": int(value)
        }
        if key in selected_ids:
            redis_cart[int(key)]['selected'] = True
        else:
            redis_cart[int(key)]['selected'] = False

    # 合并购物车
    cookie_cart_with_int.update(redis_cart)

    # 保存到redis中
    # {1:10,2:23}
    add_to_redis = {key: cookie_cart_with_int[key]['count'] for key in cookie_cart_with_int}
    # [1,2,3,4]
    add_to_redis_selected = [key for key in cookie_cart_with_int if cookie_cart_with_int[key]['selected']]

    # 写入redis
    #bug
    # redis.hmset 不能接受空字典
    # redis.sadd 不能接受空序列
    if add_to_redis:
        conn.hmset(cart_id, add_to_redis)
    if add_to_redis_selected:
        conn.sadd(cart_selected_id, *add_to_redis_selected)

    response.delete_cookie('cart')
    return response


