from rest_framework import serializers
from main.models import Cash


class CashSerializer(serializers.ModelSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Cash
        fields = ['id', 'name', 'value', 'date', 'income', 'db']
