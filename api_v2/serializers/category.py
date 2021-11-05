from django.db.models import Sum
from decimal import Decimal

from main.models import Category

from .expenditure import ExpenditureSerializer
from .DateFilterSerializer import DateFilterSerializer


class CategorySerializer(DateFilterSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Category
        fields = ['id', 'name', 'db']

    def _gen_prospect(self, representation, instance):
        prospect = {}
        prospect['expected_expenditure'] = instance.expenditures.filter(**self.gen_filters_for_month()).filter(
            is_expected=True).aggregate(Sum('value'))['value__sum'] or Decimal(0)
        prospect['actual_expenditure'] = instance.expenditures.filter(**self.gen_filters_for_month()).filter(
            is_expected=False).aggregate(Sum('value'))['value__sum'] or Decimal(0)
        prospect['delta'] = prospect['expected_expenditure'] - \
            prospect['actual_expenditure']
        representation['prospect'] = prospect

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # if self.context.get('request', DummyRequest()).method == 'GET' or getattr(self, 'include_children', False):
        representation['expected_expenditures'] = ExpenditureSerializer(
            instance.expenditures.filter(**self.gen_filters_for_month()).filter(is_expected=True), many=True, include_children=True, context=self.context).data
        representation['actual_expenditures'] = ExpenditureSerializer(
            instance.expenditures.filter(**self.gen_filters_for_month()).filter(is_expected=False), many=True, include_children=True, context=self.context).data
        self._gen_prospect(representation, instance)
        return representation
