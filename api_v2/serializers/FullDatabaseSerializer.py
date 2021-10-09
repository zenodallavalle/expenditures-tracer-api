from django.contrib.auth.models import User
from django.db.models import Sum
from main.models import Database
from rest_framework import serializers

from .cash import CashSerializer
from .category import CategorySerializer

from .utils import extract_month, extract_value, check_precedent_money_is_valid
from .DateFilterSerializer import DateFilterSerializer


class FullDatabaseSerializer(DateFilterSerializer):
    users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all())

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Database
        fields = ['id', 'name', 'users']

    def _get_actual_money(self, instance):
        return instance.cashes.filter(**self.gen_filters_for_month('reference_date')).filter(income=False).order_by('reference_date').last()

    def _get_precedent_actual_money(self, instance):
        return instance.cashes.filter(**self.gen_filters_for_precedent('reference_date')).filter(income=False).order_by('reference_date').last()

    def _gen_prospect(self, representation, instance):
        # Remember to call _gen_prospect after representation has already been added with categories and incomes
        actual_money = self._get_actual_money(instance)
        precedent_money = self._get_precedent_actual_money(instance)

        prospect = {'warn': None}
        prospect['income'] = float(instance.cashes.filter(**self.gen_filters_for_month('reference_date')).filter(
            income=True).aggregate(Sum('value'))['value__sum'] or 0.00)
        prospect['actual_money'] = float(extract_value(actual_money) or 0.00)
        prospect['expected_expenditure'] = float(instance.expenditures.filter(**self.gen_filters_for_month()).filter(
            is_expected=True).aggregate(Sum('value'))['value__sum'] or 0.00)
        prospect['actual_expenditure'] = float(instance.expenditures.filter(**self.gen_filters_for_month()).filter(
            is_expected=False).aggregate(Sum('value'))['value__sum'] or 0.00)

        if not precedent_money:
            prospect['warn'] = 'Previous month money not found.'
            prospect['delta_expenditure'] = None

        else:
            if not check_precedent_money_is_valid(self._get_actual_money(instance), precedent_money, 'reference_date'):
                prospect['warn'] = 'Previous money registration is more than a month ago'
            prospect['delta_expenditure'] = float(prospect['expected_expenditure'] -
                                                  prospect['actual_expenditure'])

        prospect['expected_saving'] = float(prospect['income'] -
                                            prospect['actual_expenditure'])
        prospect['actual_saving'] = float(actual_money.value -
                                          getattr(precedent_money, 'value', 0))
        prospect['delta_saving'] = float(prospect['actual_saving'] -
                                         prospect['expected_saving'])
        representation['prospect'] = prospect

    def _gen_months_list(self, representation, instance):
        dates = list(instance.expenditures.values_list(
            'date', flat=True))
        dates.extend(list(instance.cashes.values_list(
            'reference_date', flat=True)))
        dates = sorted(dates, reverse=True)
        months = set(map(extract_month, dates))
        representation['months_list'] = months

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # if self.context.get('request', DummyRequest()).method == 'GET' or getattr(self, 'include_children', False):
        representation['categories'] = CategorySerializer(
            instance.categories.all(), many=True, include_children=True, context=self.context).data
        representation['incomes'] = CashSerializer(
            instance.cashes.filter(**self.gen_filters_for_month('reference_date')).filter(income=True), many=True, include_children=True, context=self.context).data
        representation['actual_money'] = CashSerializer(
            self._get_actual_money(instance), include_children=True, context=self.context).data
        self._gen_prospect(representation, instance)
        self._gen_months_list(representation, instance)
        return representation
