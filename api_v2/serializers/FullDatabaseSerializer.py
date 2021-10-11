from datetime import datetime
from dateutil import relativedelta
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from main.models import Database
from rest_framework import serializers

from .cash import CashSerializer
from .category import CategorySerializer

from .utils import extract_month, extract_value, check_precedent_money_is_valid
from .DateFilterSerializer import DateFilterSerializer


class FullDatabaseSerializer(DateFilterSerializer):
    users = serializers.PrimaryKeyRelatedField(required=False,
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

        if not actual_money:
            prospect['warn'] = 'Actual money for current month not registered yet'
            prospect['delta_expenditure'] = None
        elif not precedent_money:
            prospect['warn'] = 'Previous month money not found'
            prospect['delta_expenditure'] = None
        else:
            if not check_precedent_money_is_valid(self._get_actual_money(instance), precedent_money, 'reference_date'):
                prospect['warn'] = 'Previous money registration is more than a month ago'
            prospect['delta_expenditure'] = float(prospect['expected_expenditure'] -
                                                  prospect['actual_expenditure'])

        prospect['expected_saving'] = float(prospect['income'] -
                                            prospect['actual_expenditure'])
        if not actual_money:
            prospect['actual_money'] = None
            prospect['delta_saving'] = None
        else:
            prospect['actual_saving'] = float(actual_money.value -
                                              getattr(precedent_money, 'value', 0))
            prospect['delta_saving'] = float(prospect['actual_saving'] -
                                             prospect['expected_saving'])
        representation['prospect'] = prospect

    def _gen_months_list(self, representation, instance):
        def extract_unique_dts(values):
            dts = []
            dts_d = {}
            for month, year in values:
                if f'{month}-{year}' not in dts_d:
                    dts_d[f'{month}-{year}'] = True
                    dts.append(datetime(year, month, 1))
            return dts
        dts = extract_unique_dts(instance.cashes.order_by('-reference_date').values_list(
            'reference_date__month', 'reference_date__year'))
        months_list = []
        for dt in dts:
            current_month = self.gen_current_month()
            working_month = dt.strftime('%m-%Y')
            element = {'month': working_month}
            element['is_working'] = working_month == current_month
            start_date = timezone.make_aware(dt)
            end_date = timezone.make_aware(
                dt + relativedelta.relativedelta(months=1))
            element['income'] = float(instance.cashes.filter(
                income=True, reference_date__gte=start_date, reference_date__lt=end_date).aggregate(Sum('value'))['value__sum'] or 0.00)
            months_list.append(element)
            current_money = instance.cashes.filter(
                income=False, reference_date__gte=start_date, reference_date__lt=end_date).last()
            element['warn'] = None if current_money else 'This month has no actual money registration'
            element['current_money'] = float(
                0.00 if not current_money else current_money.value)
        representation['months_list'] = months_list

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

    def create(self, validated_data):
        if not validated_data.get('users', None):
            validated_data['users'] = [self.context['request'].user]
        return super().create(validated_data)
