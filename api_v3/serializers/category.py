from django.db.models import Sum
from decimal import Decimal
from rest_framework import serializers

from main.models import Category

from .DateFilterSerializer import DateFilterSerializer
from .DBRelatedBaseSerializer import DBRelatedBaseSerializer


class CategorySerializer(DateFilterSerializer, DBRelatedBaseSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "db",
        ]

    def _gen_prospect(self, representation, instance):
        prospect = {}
        prospect["expected_expenditure"] = instance.expenditures.filter(
            **self.gen_filters_for_month()
        ).filter(is_expected=True).aggregate(Sum("value"))["value__sum"] or Decimal(0)
        prospect["actual_expenditure"] = instance.expenditures.filter(
            **self.gen_filters_for_month()
        ).filter(is_expected=False).aggregate(Sum("value"))["value__sum"] or Decimal(0)
        prospect["delta"] = (
            prospect["expected_expenditure"] - prospect["actual_expenditure"]
        )
        representation["prospect"] = prospect

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["expected_expenditures"] = serializers.PrimaryKeyRelatedField(
            many=True, read_only=True
        ).to_representation(
            instance.expenditures.filter(
                **self.gen_filters_for_month(), is_expected=True
            ).order_by("date")
        )
        representation["actual_expenditures"] = serializers.PrimaryKeyRelatedField(
            many=True, read_only=True
        ).to_representation(
            instance.expenditures.filter(
                **self.gen_filters_for_month(), is_expected=False
            ).order_by("date"),
        )

        self._gen_prospect(representation, instance)

        return representation


class GraphsCategorySerializer(DateFilterSerializer, DBRelatedBaseSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Category
        db = serializers.PrimaryKeyRelatedField(read_only=True, many=False)
        fields = [
            "id",
            "db",
            "name",
        ]

    def _gen_prospect(self, representation, instance):
        prospect = {}
        prospect["expected_expenditure"] = instance.expenditures.filter(
            **self.gen_filters_for_month()
        ).filter(is_expected=True).aggregate(Sum("value"))["value__sum"] or Decimal(0)
        prospect["actual_expenditure"] = instance.expenditures.filter(
            **self.gen_filters_for_month()
        ).filter(is_expected=False).aggregate(Sum("value"))["value__sum"] or Decimal(0)
        prospect["delta"] = (
            prospect["expected_expenditure"] - prospect["actual_expenditure"]
        )
        representation["prospect"] = prospect

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        self._gen_prospect(representation, instance)
        return representation
