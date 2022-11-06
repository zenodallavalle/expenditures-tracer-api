from rest_framework import serializers


class DateFilterSerializer(serializers.ModelSerializer):
    def gen_current_month(self):
        return self.context['request'].min_date.strftime('%m-%Y')

    def gen_filters_for_month(self, field_prefix='date'):
        filters = {}
        filters[f'{field_prefix}__gte'] = self.context['request'].min_date
        filters[f'{field_prefix}__lt'] = self.context['request'].max_date
        return filters

    def gen_filters_for_precedent(self, field_prefix='date'):
        filters = {}
        filters[f'{field_prefix}__lt'] = self.context['request'].min_date
        return filters
