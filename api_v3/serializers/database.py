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

    def _gen_months_list(self, representation, instance):
        incomes = (
            instance.cashes.filter(income=True)
            .annotate(my=models.functions.TruncMonth("reference_date"))
            .order_by("my")
            .values("my")
            .annotate(value=models.Sum("value", default=0))
            .values("my", "value")
        )
        current_moneys = (
            instance.cashes.filter(income=False)
            .annotate(my=models.functions.TruncMonth("reference_date"))
            .order_by("my")
        )
        subquery = (
            current_moneys.values("my")
            .annotate(latest=models.Max("reference_date"))
            .filter(pk=models.OuterRef("pk"))
            .values("latest")
        )

        current_moneys = (
            current_moneys.annotate(latest=models.Subquery(subquery))
            .values("my")
            .annotate(
                latest_value=models.Sum(
                    "value",
                    default=0,
                    filter=models.Q(reference_date=models.F("latest")),
                )
            )
            .values("my", "latest_value")
        )
        months_available = set()
        incomes_dict = {}
        current_moneys_dict = {}

        for i in incomes:
            months_available.add(i["my"])
            incomes_dict[i["my"].strftime("%m-%Y")] = i["value"]
        for i in current_moneys:
            months_available.add(i["my"])
            current_moneys_dict[i["my"].strftime("%m-%Y")] = i["latest_value"]

        months_available = sorted(months_available, reverse=True)

        months_list = []
        current_month = self.gen_current_month()

        for i, dt in enumerate(months_available):
            working_month = dt.strftime("%m-%Y")

            if i == len(months_available) - 1:
                prev_month_actual_money = getattr(
                    (
                        pmam := self._get_precedent_actual_money_for_month(
                            instance, lt=dt
                        )
                    ),
                    "value",
                    Decimal(0),
                )
                prev_month_available = bool(pmam)
            else:

                prev_month_actual_money = current_moneys_dict.get(
                    months_available[i + 1].strftime("%m-%Y"), Decimal(0)
                )
                prev_month_available = True

            element = {
                "month": working_month,
                "is_working": working_month == current_month,
                "income": (income := incomes_dict.get(working_month, Decimal(0))),
                "current_money": (
                    cm := current_moneys_dict.get(working_month, Decimal(0))
                ),
                "warn": (
                    None
                    if prev_month_available
                    else "This month has no actual money registration"
                ),
                "expenditure": (cm - prev_month_actual_money - income),
                "previous_month_actual_money": prev_month_actual_money,
            }

            months_list.append(element)

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
