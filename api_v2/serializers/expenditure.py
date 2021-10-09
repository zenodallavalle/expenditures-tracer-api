from django.core.exceptions import ValidationError
from rest_framework import serializers

from main.models import Expenditure

from .DateFilterSerializer import DateFilterSerializer


class ExpenditureSerializer(DateFilterSerializer):
    expected_expenditure = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                              queryset=Expenditure.objects.filter(is_expected=True))

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Expenditure
        fields = ['id', 'name', 'value', 'date', 'expected_expenditure',
                  'is_expected', 'category', 'user', 'db']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.is_expected:
            representation['actual_expenditures'] = serializers.PrimaryKeyRelatedField(
                instance.actual_expenditures, many=True)
        return representation

    def validate(self, attrs):
        if attrs['is_expected'] and attrs['expected_expenditure'] is not None:
            raise ValidationError(
                'Expenditure cannot be expected and have expected_expenditure at the same time.')
        return super().validate(attrs)
