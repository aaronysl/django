import time

from decimal import Decimal
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers
from django.db import transaction

from goods.models import SKU

from .models import OrderGoods, OrderInfo


class OrderSkuSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(label='数量', read_only=True)

    class Meta:
        model = SKU
        fields = ['id', 'count', 'name', 'price', 'default_image_url']


class OrderCreateSerializer(serializers.Serializer):
    order_id = serializers.CharField(label='订单编号', read_only=True)
    address = serializers.IntegerField(label="收货地址", write_only=True)
    pay_method = serializers.IntegerField(label='支付方式', write_only=True)

    # 数据校验

    def create(self, validated_data):
        user = self.context['request'].user
        # 构建订单编号
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        total_amount = Decimal(0)
        total_count = 0

        # 循环迭代
        conn = get_redis_connection('cart')
        cart_id = 'cart_%d' % user.id
        cart_selected_id = 'cart_selected_%d' % user.id
        # {
        #     sku_id:count
        #     b'1':b'10'
        # }
        sku_ids = conn.hgetall(cart_id)
        # {b'1',b'2'}
        cart_selected_ids = conn.smembers(cart_selected_id)
        #事务
        with transaction.atomic():
            save_point = transaction.savepoint()
            try:
                # 创建基本订单对象
                order = OrderInfo()
                order.user = user
                order.order_id = order_id
                order.address_id = validated_data['address']
                order.freight = Decimal(10)
                order.total_amount = Decimal(0)
                order.pay_method = validated_data['pay_method']
                order.save()

                for sku_id in cart_selected_ids:
                    lool_time = 0
                    while True:
                        sku = SKU.objects.get(id=int(sku_id))
                        count = int(sku_ids[sku_id])
                        price = sku.price
                        # 判断商品库存
                        if count > sku.stock:
                            raise serializers.ValidationError('%s 库存不足' % sku.name)

                        # 更新库存
                        sku_stock = sku.stock
                        last_stock = sku.stock - count
                        # 计算总价
                        total_amount += price * Decimal(count)
                        # 计算商品总数
                        total_count += count

                        # sku.stock = last_stock
                        # sku.save()
                        #更新的时候判断库存是否被修改
                        update_count = SKU.objects.filter(id=sku.id, stock=sku_stock).update(stock=last_stock)

                        if update_count == 0:
                            # 说明商品库存已经被修改
                            lool_time += 1
                            if lool_time >= 5:
                                raise Exception('当前业务繁忙,轻稍后再试')
                            continue

                        # 保存订单详情
                        order_goods = OrderGoods()
                        order_goods.order = order
                        order_goods.sku = sku
                        order_goods.count = count
                        order_goods.price = price
                        order_goods.save()
                        break
                # 更新订单总价和商品总数
                order.total_amount = total_amount
                order.total_count = total_count
                order.save()
            except Exception:
                transaction.savepoint_rollback(save_point)
                raise
            else:
                transaction.savepoint_commit(save_point)
        # 删除已经生成订单的商品
        if cart_selected_ids:
            conn.srem(cart_selected_id, *cart_selected_ids)
            conn.hdel(cart_id, *cart_selected_ids)

        return order
