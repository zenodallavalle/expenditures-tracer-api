from rest_framework.exceptions import MethodNotAllowed, ParseError, bad_request
from rest_framework.utils import representation
from .exceptions import NotAllowedAction
import json
from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from api_v2.serializers.user import PublicUserSerializer
from main.models import Database, Cash, Category, Expenditure
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .permissions import DBPermission, DBRelatedPermission
from api_v2.serializers import PrivateUserSerializer, PublicUserSerializer, CategorySerializer, SimpleDatabaseSerializer, FullDatabaseSerializer, CashSerializer, ExpenditureSerializer


def validate_month(val):
    try:
        month, year = val.split('-')
        month = int(month)
        year = int(year)
        if month <= 12 and month >= 1:
            return month, year
    except Exception as e:
        print(e)
        return None, None


def get_month_year():
    n = datetime.now()
    return n.month, n.year


def get_months(request):
    try:
        # the idea is to gather a list of unique combination of ref_date_month and ref_date_year and
        # then to iterate through them in order to retrieve income and actual_cash for every single month
        db = Database.objects.filter(id=request.GET['db__id']).first()
        dts = []
        list_values = list(db.expenditures.all().values_list(
            'date__month', 'date__year'))
        list_values.extend(list(db.cashes.all().values_list(
            'reference_date__month', 'reference_date__year')))
        for v in list_values:
            dt = datetime(v[1], v[0], 1, 0, 0, 0)
            if dt not in dts:
                dts.append(dt)
        dts = sorted(dts, reverse=True)

        data = []
        for dt in dts:
            res = [dt.strftime('%m-%Y')]
            start_date = timezone.make_aware(dt)
            end_date = timezone.make_aware(dt + relativedelta(months=1))

            income = sum(db.cashes.filter(
                income=True,
                reference_date__gte=start_date,
                reference_date__lt=end_date
            ).values_list('value', flat=True))
            res.append(income)

            current_money = db.cashes.filter(
                income=False,
                reference_date__gte=start_date,
                reference_date__lt=end_date
            ).order_by('-date').first()
            if not current_money:
                last_current_money = db.cashes.filter(
                    income=False,
                    reference_date__lt=start_date
                ).order_by('-date').first()
                precedent_month_current_money_value = last_current_money.value if last_current_money else 0
                current_money = Cash.objects.create(
                    value=precedent_month_current_money_value, name='', db=db, reference_date=start_date)
            res.append(current_money.value)
            data.append(res)
        return JsonResponse({'results': data})
    except Exception as e:
        print(e)
        raise Http404


def copy_from_precedent_month(request):
    try:
        user = Token.objects.filter(key=request.headers['authorization'].rsplit(' ')[-1]
                                    ).first().user
        assert request.method == 'GET'
        db = Database.objects.filter(id=request.GET['db__id']).first()
        month, year = validate_month(request.GET['month'])
        end_date_unaware = datetime(year, month, 1, 0, 0, 0)
        end_date = timezone.make_aware(end_date_unaware)
        start_date = timezone.make_aware(
            end_date_unaware - relativedelta(months=1))
        qs = db.expenditures.filter(
            date__gte=start_date, date__lt=end_date, is_expected=True)
        for exp in qs:
            print('doubling exp', exp.name)
            Expenditure.objects.create(
                name=exp.name,
                value=exp.value,
                is_expected=True,
                date=(exp.date+relativedelta(months=1)),
                category=exp.category,
                user=user
            )
        return HttpResponse(json.dumps({'status': 'OK'}))
    except Exception as e:
        print(e)
        raise ParseError


class ExtendedAuthToken(ObtainAuthToken):
    def _not_authenticated(self):
        r = JsonResponse({'detail': 'Invalid or missing token.'})
        r.status_code = 401
        return r

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return JsonResponse(PrivateUserSerializer(context={'request': request}).to_representation(request.user))
        return self._not_authenticated()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        request.user = user
        Token.objects.get_or_create(user=user)
        return JsonResponse(PrivateUserSerializer(context={'request': request}).to_representation(request.user))


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = PublicUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = permissions.SAFE_METHODS
    queryset = User.objects.all()


class ModelViewSetWithoutRetrieve(viewsets.ModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        raise NotAllowedAction('retrieve')


class ModelViewSetWithoutList(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        raise NotAllowedAction('list')


class DBRelatedViewSet(viewsets.ModelViewSet):
    permission_classes = [DBRelatedPermission]
    http_method_names = ['options', 'head',
                         'post', 'patch', 'update', 'delete']

    def get_queryset(self):
        queryset = self.model.objects.filter(db__users__in=[self.request.user])
        return queryset

    def destroy(self, request, *args, **kwargs):
        if not getattr(self.serializer_class, 'destroy', None):
            return super().destroy(request, *args, **kwargs)
        else:
            instance = self.get_object()
            representation = self.serializer_class(instance).destroy(instance)
            return JsonResponse(representation)


class DatabaseViewSet(ModelViewSetWithoutList):
    serializer_class = FullDatabaseSerializer
    permission_classes = [DBPermission]

    def _analyze_request_month(self):
        reference_month = self.request.params.get('reference_month', None)
        if reference_month:
            month, year = [int(x.strip())
                           for x in reference_month.split('-')[:2]]
        else:
            n = datetime.now()
            month = n.month
            year = n.year
        min_date = datetime(year, month, 1)
        max_date = min_date + relativedelta(months=1)
        self.request.min_date = timezone.make_aware(min_date)
        self.request.max_date = timezone.make_aware(max_date)

    def get_queryset(self):
        queryset = Database.objects.filter(users__in=[self.request.user])
        return queryset

    def retrieve(self, request, *args, **kwargs):
        self._analyze_request_month()
        return super().retrieve(request, *args, **kwargs)


class CashViewSet(DBRelatedViewSet, ModelViewSetWithoutList, ModelViewSetWithoutRetrieve):
    model = Cash
    serializer_class = CashSerializer


class CategoryViewSet(DBRelatedViewSet, ModelViewSetWithoutList, ModelViewSetWithoutRetrieve):
    model = Category
    serializer_class = CategorySerializer


class ExpenditureViewSet(DBRelatedViewSet, ModelViewSetWithoutList, ModelViewSetWithoutRetrieve):
    model = Expenditure
    serializer_class = ExpenditureSerializer
