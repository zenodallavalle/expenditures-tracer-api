from rest_framework import serializers

from main.models import Expenditure


class ExpenditureSerializer(serializers.ModelSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Expenditure
        fields = ['id', 'name', 'value', 'date',
                  'is_expected', 'category', 'user', 'db']
