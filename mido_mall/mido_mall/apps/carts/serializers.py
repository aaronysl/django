from rest_framework import serializers

from goods.models import SKU


class CartSkuSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(label='数量', read_only=True)
    selected = serializers.BooleanField(label='勾选', read_only=True)

    class Meta:
        model = SKU
        fields = ['id', 'count', 'name', 'price', 'default_image_url', 'selected']
