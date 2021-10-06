from django.contrib.auth.models import User
from main.models import Database
from rest_framework import serializers

from .cash import CashSerializer
from .category import CategorySerializer


class FullDatabaseSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all())

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Database
        fields = ['id', 'name', 'users']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # if self.context.get('request', DummyRequest()).method == 'GET' or getattr(self, 'include_children', False):
        representation['categories'] = CategorySerializer(
            instance.categories.all(), many=True, include_children=True).data
        representation['incomes'] = CashSerializer(
            instance.cashes.filter(income=True), many=True, include_children=True).data
        representation['actual_money'] = CashSerializer(
            instance.cashes.filter(income=False).first(), include_children=True).data
        return representation
