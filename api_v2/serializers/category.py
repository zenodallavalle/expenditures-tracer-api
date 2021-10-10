from django.db.models import Sum

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
        prospect['expected_expenditure'] = float(instance.expenditures.filter(**self.gen_filters_for_month()).filter(
            is_expected=True).aggregate(Sum('value'))['value__sum'] or 0.00)
        prospect['actual_expenditure'] = float(instance.expenditures.filter(**self.gen_filters_for_month()).filter(
            is_expected=False).aggregate(Sum('value'))['value__sum'] or 0.00)
        prospect['delta'] = prospect['actual_expenditure'] - \
            prospect['expected_expenditure']
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

    def update(self, instance, validated_data):
        print('update category', validated_data)
        return super().update(instance, validated_data)
