from rest_framework import serializers


class DateFilterSerializer(serializers.ModelSerializer):
    def gen_current_month(self):
        return self.context["request"].min_date.strftime("%m-%Y")

    def gen_filters_for_month(self, field_prefix="date", lt=None, gte=None):
        filters = {}
        filters[f"{field_prefix}__gte"] = (
            self.context["request"].min_date if gte is None else gte
        )
        filters[f"{field_prefix}__lt"] = (
            self.context["request"].max_date if lt is None else lt
        )
        return filters

    def gen_filters_for_precedent(self, field_prefix="date", lt=None):
        filters = {}
        filters[f"{field_prefix}__lt"] = (
            self.context["request"].min_date if lt is None else lt
        )
        return filters
