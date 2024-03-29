from decimal import Decimal
from django.db.models import Sum
from django.core.exceptions import ValidationError
from rest_framework import serializers
from django.utils import timezone
from main.models import Expenditure

from .DateFilterSerializer import DateFilterSerializer
from .DBRelatedBaseSerializer import DBRelatedBaseSerializer


class ExpenditureSerializer(DateFilterSerializer, DBRelatedBaseSerializer):
    expected_expenditure = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Expenditure.objects.filter(is_expected=True),
    )
    actual_expenditures = serializers.PrimaryKeyRelatedField(
        read_only=True, many=True, allow_null=True
    )

    user = serializers.PrimaryKeyRelatedField(required=False, read_only=True)

    date = serializers.DateTimeField()

    class Meta:
        model = Expenditure
        fields = [
            'id',
            'name',
            'value',
            'date',
            'expected_expenditure',
            'is_expected',
            'category',
            'user',
            'db',
            'actual_expenditures',
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        prospect = {}
        if representation['is_expected']:
            representation.pop('expected_expenditure')

            prospect['actual'] = instance.actual_expenditures.all().aggregate(
                Sum('value')
            )['value__sum'] or Decimal(0)
            prospect['expected'] = representation['value']
            prospect['delta'] = instance.value - prospect['actual']

        else:
            representation.pop('actual_expenditures')

            if instance.expected_expenditure:
                prospect[
                    'actual'
                ] = instance.expected_expenditure.actual_expenditures.all().aggregate(
                    Sum('value')
                )[
                    'value__sum'
                ]
                prospect['expected'] = instance.expected_expenditure.value
                prospect['delta'] = prospect['expected'] - prospect['actual']
            else:
                prospect['actual'] = representation['value']
                prospect['expected'] = None
                prospect['delta'] = None

        representation['prospect'] = prospect
        return representation

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        if attrs.get('is_expected', None) and attrs.get('expected_expenditure', None):
            raise ValidationError(
                'Expenditure cannot be expected and have expected_expenditure at the same time.'
            )
        if attrs.get('expected_expenditure', None):
            if attrs['expected_expenditure'].category.pk != attrs.get('category', None):
                attrs['category'] = attrs['expected_expenditure'].category
        return super().validate(attrs)
