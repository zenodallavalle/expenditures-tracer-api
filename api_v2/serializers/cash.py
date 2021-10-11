from rest_framework import serializers
from main.models import Cash
from .DateFilterSerializer import DateFilterSerializer


class CashSerializer(DateFilterSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    reference_date = serializers.DateTimeField(required=False)

    class Meta:
        model = Cash
        fields = ['id', 'name', 'value', 'date',
                  'reference_date', 'income', 'db']

    def create(self, validated_data):
        if not validated_data.get('reference_date', None):
            validated_data['reference_date'] = self.context['request'].min_date
        return super().create(validated_data)
