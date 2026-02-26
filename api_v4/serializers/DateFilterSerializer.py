from rest_framework import serializers


class DateFilterSerializer(serializers.ModelSerializer):
    def gen_current_month(self):
        return self.context["request"].min_date.strftime("%m-%Y")

    def gen_filters_for_month(self, field_prefix="date", lt=None, gte=None):
        filters = {}
        filters[f"{field_prefix}__gte"] = gte or self.context["request"].min_date
        filters[f"{field_prefix}__lt"] = lt or self.context["request"].max_date
        return filters

    def gen_filters_for_precedent(self, field_prefix="date", lt=None):
        filters = {}
        filters[f"{field_prefix}__lt"] = lt or self.context["request"].min_date
        return filters

    def gen_filters_for_month_list(self, field_prefix="date", lte=None, gte=None):
        filters = {}
        filters[f"{field_prefix}__gte"] = (
            gte or self.context["request"].request_month_list_gte
        )
        filters[f"{field_prefix}__lte"] = (
            lte or self.context["request"].request_month_list_lte
        )
        return filters
