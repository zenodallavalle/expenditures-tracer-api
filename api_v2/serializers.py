from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Database, Cash, Category, Expenditure
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from rest_framework import serializers
from decimal import Decimal


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


def get_month_year(n=datetime.now()):
    return n.month, n.year


class DbsPKRField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request')
        if request:
            if request.user.is_authenticated:
                return request.user.dbs.all()


class CategoriesPKRField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request')
        if request:
            if request.user.is_authenticated:
                return Category.objects.filter(db__in=request.user.dbs.all())


class ExpendituresPKRField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request')
        if request:
            if request.user.is_authenticated:
                return Expenditure.objects.filter(db__in=request.user.dbs.all(), is_expected=True)


class CashSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=128, allow_null=True)
    value = serializers.DecimalField(max_digits=11, decimal_places=2)
    date = serializers.DateTimeField(required=False, allow_null=True)
    income = serializers.BooleanField(default=False)
    reference_date = serializers.DateTimeField(required=False, allow_null=True)
    db = DbsPKRField()

    class Meta:
        model = Cash
        fields = ['id', 'name', 'value', 'date',
                  'income', 'db', 'reference_date']

    def _get_user(self):
        request = self.context.get('request')
        if request:
            return request.user

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.value = validated_data.get('value', instance.value)
        instance.save()
        return instance


class ExpenditureSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=128, required=True)
    value = serializers.DecimalField(max_digits=11, decimal_places=2)
    date = serializers.DateTimeField(required=False, allow_null=True)
    is_expected = serializers.BooleanField(default=False)

    expected_expenditure = ExpendituresPKRField(
        required=False, allow_null=True)
    actual_expenditures = ExpendituresPKRField(many=True, read_only=True)
    category = CategoriesPKRField()

    class Meta:
        model = Expenditure
        fields = ['id', 'name', 'value', 'date', 'category',
                  'is_expected', 'expected_expenditure', 'actual_expenditures']

    def _get_user(self):
        request = self.context.get('request')
        if request:
            return request.user

    def create(self, validated_data):
        name = validated_data.get('name')
        value = validated_data.get('value')
        date = validated_data.get('date')
        is_expected = validated_data.get('is_expected', False)
        category = validated_data.get('category')
        user = self._get_user()
        expected_expenditure = None
        if not is_expected:
            # expected expenditure, can not have related expected expenditure
            # get expected_expenditure and check if it is coherent
            try:
                expected_expenditure = validated_data.pop(
                    'expected_expenditure')
                if expected_expenditure:
                    # use this category
                    category = expected_expenditure.category
            except Exception as e:
                pass
        obj = Expenditure.objects.create(name=name,
                                         value=value,
                                         date=date,
                                         is_expected=is_expected,
                                         category=category,
                                         expected_expenditure=expected_expenditure,
                                         user=user)
        print('category:', obj.category, 'name:', obj.name,
              'expected_expenditure', obj.expected_expenditure)
        # print(obj.__dict__)
        return obj

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.value = validated_data.get('value', instance.value)
        instance.date = validated_data.get('date', instance.date)
        print('date:', type(instance.date), instance.date)
        # maybe this conditions shold stay in model.save
        category = validated_data.get('category')
        if not instance.is_expected:
            # get expected_expenditure and check if it is coherent
            expected_expenditure = validated_data.get(
                'expected_expenditure', None)
            if expected_expenditure:
                # obtain category
                category = expected_expenditure.category
            # link with expected_expenditure
            instance.expected_expenditure = expected_expenditure
            if instance.category.id != category.id:
                # update category
                instance.category = category
                # remove link with precedent actual expenditures
                instance.actually_expenditures.clear()
        instance.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=128, required=True)
    db = DbsPKRField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'db']

    def _get_user(self):
        request = self.context.get('request')
        if request:
            return request.user

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context['request']
        month, year = get_month_year()
        if request.method == 'GET':
            if 'month' in request.GET:
                month, year = validate_month(request.GET['month'])
        start_date = timezone.make_aware(datetime(year, month, 1, 0, 0, 0))
        end_date = start_date + relativedelta(months=1)
        output = super(CategorySerializer, self).to_representation(instance)
        output['expected_expenditure'] = sum(instance.expenditures.filter(
            is_expected=True, date__gte=start_date, date__lt=end_date).values_list('value', flat=True))
        output['actual_expenditure'] = sum(instance.expenditures.filter(
            is_expected=False, date__gte=start_date, date__lt=end_date).values_list('value', flat=True))
        output['delta'] = output['expected_expenditure'] - \
            output['actual_expenditure']
        return output


class DatabaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=128, required=True)
    categories = CategorySerializer(
        many=True, read_only=True)

    class Meta:
        model = Database
        #fields = ['id', 'name']
        fields = ['id', 'name', 'categories']

    def _get_user(self):
        request = self.context.get('request')
        if request:
            return request.user

    def create(self, validated_data):
        '''
        create and return new Database instance, given validated data.
        '''
        users = [self._get_user()]
        db = Database.objects.create(**validated_data)
        db.users.set(users)
        return db

    def update(self, instance, validated_data):
        '''
        Update and return an existing Database instance, given validated data.
        '''
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context['request']
        month, year = get_month_year()
        if request.method == 'GET':
            if 'month' in request.GET:
                month, year = validate_month(request.GET['month'])
        start_date_unaware = datetime(year, month, 1, 0, 0, 0)
        start_date = timezone.make_aware(start_date_unaware)
        end_date = timezone.make_aware(
            start_date_unaware + relativedelta(months=1))
        output = super(DatabaseSerializer,
                       self).to_representation(instance)
        output['income'] = sum(instance.cashes.filter(
            income=True, reference_date__gte=start_date, reference_date__lt=end_date).values_list('value', flat=True))
        current_money = instance.cashes.filter(
            income=False, reference_date__gte=start_date, reference_date__lt=end_date).order_by('-date').first()
        # if current_money:
        #print('current money found', current_money.__dict__)
        # print(current_money)
        if not current_money:
            #print('current money not found')
            #prec_month, prec_year = get_month_year(datetime(year, month, 1,0,0,0)-relativedelta(months=1))
            #end_date = datetime(prec_year, prec_month, 1, 0, 0, 0)
            #upper_date_limit = start_date - relativedelta(months=1)
            precedent_month_current_money = instance.cashes.filter(
                income=False,
                reference_date__lt=start_date
            ).order_by('-date').order_by('-reference_date').first()
            # print(precedent_month_current_money)
            # print(n)
            precedent_month_current_money_value = precedent_month_current_money.value if precedent_month_current_money else 0
            current_money = Cash.objects.create(
                value=precedent_month_current_money_value, name='', db=instance, reference_date=start_date)
        current_money_dict = CashSerializer(current_money).data
        output['actual_expenditure'] = sum(instance.expenditures.filter(
            is_expected=False, date__gte=start_date, date__lt=end_date).values_list('value', flat=True))
        output['expected_expenditure'] = sum(instance.expenditures.filter(
            is_expected=True, date__gte=start_date, date__lt=end_date).values_list('value', flat=True))
        output['delta_expenditure'] = output['expected_expenditure'] - \
            output['actual_expenditure']
        output['current_money'] = current_money_dict
        #end_date = datetime(year, month, 1, 0, 0, 0)-relativedelta(months=1)
        #print('end_date', end_date)
        # error here, precedent_month_current_money_value still 0
        precedent_month_current_money = instance.cashes.filter(
            income=False, reference_date__lt=start_date).order_by('-date').order_by('-reference_date').first()
        precedent_month_current_money_value = precedent_month_current_money.value if precedent_month_current_money else 0
        output['actual_saving'] = current_money.value - \
            precedent_month_current_money_value
        output['expected_saving'] = output['income'] - \
            output['actual_expenditure']
        output['delta_saving'] = output['actual_saving'] - \
            output['expected_saving']
        # print(output)
        return output


class UserSerializer(serializers.ModelSerializer):
    dbs = DatabaseSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'dbs']
