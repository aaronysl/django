from haystack import indexes
from .models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    # text = indexes.CharField(document=True, use_template=True)
    price = indexes.DecimalField(model_attr='price')
    id = indexes.IntegerField(model_attr='id')
    comments = indexes.IntegerField(model_attr='comments')
    default_image_url = indexes.CharField(model_attr='default_image_url')

    def get_model(self):
        return SKU

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)
