from django.core.exceptions import ValidationError
from rest_framework import serializers

from main.models import Expenditure

from .DateFilterSerializer import DateFilterSerializer


class ExpenditureSerializer(DateFilterSerializer):
    expected_expenditure = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                              queryset=Expenditure.objects.filter(is_expected=True))
    actual_expenditures = serializers.PrimaryKeyRelatedField(
        read_only=True, many=True)

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Expenditure
        fields = ['id', 'name', 'value', 'date', 'expected_expenditure',
                  'is_expected', 'category', 'user', 'db', 'actual_expenditures']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.is_expected:
            representation.pop('expected_expenditure')
        else:
            representation.pop('actual_expenditures')
            # try:
            #     representation['actual_expenditures'] = serializers.PrimaryKeyRelatedField(
            #         many=True, read_only=True).to_representation(instance.actual_expenditures)
            # except Exception as e:
            #     print(e)
            #     print(instance.actual_expenditures)
        return representation

    def validate(self, attrs):
        if attrs['is_expected'] and attrs['expected_expenditure'] is not None:
            raise ValidationError(
                'Expenditure cannot be expected and have expected_expenditure at the same time.')
        return super().validate(attrs)
