from django.db import models
from datetime import datetime
from dateutil import relativedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Database, Cash
from rest_framework import serializers

from .category import GraphsCategorySerializer
from .utils import extract_value, check_precedent_money_is_valid
from .DateFilterSerializer import DateFilterSerializer


class FullDatabaseSerializer(DateFilterSerializer):
    users = serializers.PrimaryKeyRelatedField(
        required=False, many=True, queryset=User.objects.all()
    )

    categories = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Database
        fields = ["id", "name", "users", "categories"]

    def _get_actual_money(self, instance):
        return (
            instance.cashes.filter(**self.gen_filters_for_month("reference_date"))
            .filter(income=False)
            .order_by("reference_date")
            .last()
        )

    def _get_precedent_actual_money(self, instance):
        return (
            instance.cashes.filter(**self.gen_filters_for_precedent("reference_date"))
            .filter(income=False)
            .order_by("reference_date")
            .last()
        )

    def _get_precedent_actual_money_for_month(self, instance, lt):
        return (
            instance.cashes.filter(
                **self.gen_filters_for_precedent("reference_date", lt=lt),
            )
            .filter(income=False)
            .order_by("reference_date")
            .last()
        )

    def _gen_prospect(self, representation, instance):
        # Remember to call _gen_prospect after representation has already been added with categories and incomes
        actual_money = self._get_actual_money(instance)
        precedent_money = self._get_precedent_actual_money(instance)

        prospect = {"warn": None}
        prospect["income"] = (
            instance.cashes.filter(**self.gen_filters_for_month("reference_date"))
            .filter(income=True)
            .aggregate(models.Sum("value", default=0))["value__sum"]
        )
        prospect["actual_money"] = extract_value(actual_money) or Decimal(0)
        prospect["expected_expenditure"] = (
            instance.expenditures.filter(**self.gen_filters_for_month())
            .filter(is_expected=True)
            .aggregate(models.Sum("value", default=0))["value__sum"]
        )
        prospect["actual_expenditure"] = (
            instance.expenditures.filter(**self.gen_filters_for_month())
            .filter(is_expected=False)
            .aggregate(models.Sum("value", default=0))["value__sum"]
        )

        if not actual_money:
            prospect["warn"] = "Actual money for current month not registered yet"

        elif not precedent_money:
            prospect["warn"] = "Previous month money not found"
        else:
            if not check_precedent_money_is_valid(
                self._get_actual_money(instance), precedent_money, "reference_date"
            ):
                prospect["warn"] = (
                    "Previous money registration is more than a month ago"
                )
        prospect["delta_expenditure"] = (
            prospect["expected_expenditure"] - prospect["actual_expenditure"]
        )

        prospect["expected_saving"] = (
            prospect["income"] - prospect["actual_expenditure"]
        )
        if not actual_money:
            prospect["actual_saving"] = None
            prospect["delta_saving"] = None
        else:
            prospect["actual_saving"] = actual_money.value - getattr(
                precedent_money, "value", Decimal(0)
            )
            prospect["delta_saving"] = (
                prospect["actual_saving"] - prospect["expected_saving"]
            )
        representation["prospect"] = prospect

    def _get_month_list(self, instance):
        return (
            instance.cashes.annotate(my=models.functions.TruncMonth("reference_date"))
            .values_list("my", flat=True)
            .union(
                instance.expenditures.annotate(
                    my=models.functions.TruncMonth("date")
                ).values_list("my", flat=True)
            )
            .order_by("-my")
        )

    def _gen_months_list(self, representation, instance):
        months_list = []

        for dt in self._get_month_list(instance):
            current_month = self.gen_current_month()
            working_month = dt.strftime("%m-%Y")
            element = {
                "month": working_month,
                "is_working": working_month == current_month,
            }

            start_date = dt
            end_date = dt + relativedelta.relativedelta(months=1)
            element["income"] = instance.cashes.filter(
                income=True, reference_date__gte=start_date, reference_date__lt=end_date
            ).aggregate(models.Sum("value"))["value__sum"] or Decimal(0)
            months_list.append(element)
            current_money = instance.cashes.filter(
                income=False,
                reference_date__gte=start_date,
                reference_date__lt=end_date,
            ).last()
            last_month_actual_money = self._get_precedent_actual_money_for_month(
                instance, lt=start_date
            )
            element["warn"] = (
                None if current_money else "This month has no actual money registration"
            )
            element["current_money"] = (
                Decimal(0) if not current_money else current_money.value
            )
            element["expenditure"] = (
                element["current_money"]
                - getattr(last_month_actual_money, "value", Decimal(0))
                - element["income"]
            )
            element["previous_month_actual_money"] = getattr(
                last_month_actual_money, "value", Decimal(0)
            )

        representation["months_list"] = months_list

    def _gen_time_boundaries(self, representation, instance):
        cash_bounds = instance.cashes.aggregate(
            min=models.Min("reference_date"), max=models.Max("reference_date")
        )
        expenditure_bounds = instance.expenditures.aggregate(
            min=models.Min("date"), max=models.Max("date")
        )

        min_dt = min(
            cash_bounds["min"] if cash_bounds["min"] else timezone.now(),
            expenditure_bounds["min"] if expenditure_bounds["min"] else timezone.now(),
        )

        min_dt = min_dt.replace(day=1)

        max_dt = max(
            cash_bounds["max"] if cash_bounds["max"] else timezone.now(),
            expenditure_bounds["max"] if expenditure_bounds["max"] else timezone.now(),
        )
        max_dt = max_dt.replace(day=1)

        representation["time_boundaries"] = {
            "start": min_dt.strftime("%m-%Y"),
            "end": max_dt.strftime("%m-%Y"),
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["incomes"] = serializers.PrimaryKeyRelatedField(
            many=True, read_only=True
        ).to_representation(
            instance.cashes.filter(
                **self.gen_filters_for_month("reference_date")
            ).filter(income=True)
        )

        representation["actual_money"] = getattr(
            self._get_actual_money(instance), "id", None
        )

        self._gen_prospect(representation, instance)
        self._gen_months_list(representation, instance)
        self._gen_time_boundaries(representation, instance)
        return representation

    def create(self, validated_data):
        if not validated_data.get("users", None):
            validated_data["users"] = [self.context["request"].user]
        return super().create(validated_data)


class GraphDatabaseSerializer(FullDatabaseSerializer, DateFilterSerializer):
    categories = GraphsCategorySerializer(read_only=True, many=True)

    def to_representation(self, instance):
        representation = super(DateFilterSerializer, self).to_representation(instance)

        return representation
