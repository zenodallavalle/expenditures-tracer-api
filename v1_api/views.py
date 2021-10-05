from rest_framework.exceptions import ParseError
import json
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from main.models import Database, Cash, Category, Expenditure
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .permissions import UserPermission, DBPermission, DBRelatedPermission
from .serializers import UserSerializer, DatabaseSerializer, CashSerializer, CategorySerializer, ExpenditureSerializer


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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
        })


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, UserPermission]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class DatabaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Databases to viewed or edited
    """
    serializer_class = DatabaseSerializer
    permission_classes = [permissions.IsAuthenticated, DBPermission]

    def get_queryset(self):
        '''
        available parameters: name, category__name
        '''
        user = self.request.user
        queryset = user.dbs.order_by('pk')
        for param in self.request.GET:
            if param == 'name':
                queryset = queryset.filter(
                    name__icontains=self.request.GET[param])
        return queryset


class CashViewSet(viewsets.ModelViewSet):
    serializer_class = CashSerializer
    permission_classes = [permissions.IsAuthenticated, DBRelatedPermission]

    def get_queryset(self):
        '''
        available parameters: name, category__name
        '''
        queryset = Cash.objects.all()
        if self.request.method == 'GET':
            if 'month' in self.request.GET:
                month, year = validate_month(self.request.GET['month'])
            else:
                month, year = get_month_year()
            start_date_unaware = datetime(year, month, 1, 0, 0, 0)
            start_date = timezone.make_aware(start_date_unaware)
            end_date = timezone.make_aware(
                start_date_unaware + relativedelta(months=1))
            # use -> reference_date__gte=start_date, reference_date__lt=end_date

            db__id = self.request.GET['db__id']
            db = Database.objects.filter(id=db__id).first()
            if not db:
                raise Http404
            queryset = db.cashes.filter(income=True)
            '''if not queryset.filter(income=False, reference_date__year=year, reference_date__month=month).exists():
                n = timezone.make_aware(
                    datetime(year=year, month=month, day=1, hour=0, minute=0,second=0))
                Cash(db=db, name='', value=0, reference_date=n).save()
                queryset = db.cashes.all()'''
            queryset = queryset.filter(
                reference_date__gte=start_date, reference_date__lt=end_date)
            for exp in queryset:
                print('cash found exp', exp.name, 'value:',
                      exp.value, 'ref_date', exp.reference_date)
        return queryset.order_by('-date')


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, DBRelatedPermission]

    def get_queryset(self):
        user = self.request.user
        if self.request.method == 'GET':
            queryset = Database.objects.filter(
                id=self.request.GET['db__id']).first().categories.all()
            queryset = queryset.order_by('pk')
        else:
            queryset = Category.objects.all()
        return queryset


class ExpenditureViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenditureSerializer
    permission_classes = [permissions.IsAuthenticated, DBRelatedPermission]

    def get_queryset(self):
        user = self.request.user
        if self.request.method == 'GET':
            queryset = Database.objects.filter(
                id=self.request.GET['db__id']).first().expenditures.all()
            queryset = queryset.order_by('-date')
        else:
            queryset = Expenditure.objects.all()
        if 'month' in self.request.GET:
            month, year = validate_month(self.request.GET['month'])
        else:
            month, year = get_month_year()
        queryset = queryset.filter(date__year=year, date__month=month)
        return queryset
