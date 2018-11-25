from rest_framework import serializers

from .models import SKU


class SkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'comments', 'default_image_url']
