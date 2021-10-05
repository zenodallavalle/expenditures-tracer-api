from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


class Database(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(to=User, related_name='dbs')
    name = models.CharField(max_length=128)

    def __repr__(self):
        return '<class Database: {}, users:{}>'.format(self.name, ', '.join([i.username for i in self.users.all()]))

    def __str__(self):
        return self.name


class Cash(models.Model):
    name = models.CharField(max_length=128, null=True)
    value = models.DecimalField(max_digits=11, decimal_places=2)
    date = models.DateTimeField(auto_now=True)
    reference_date = models.DateTimeField()
    # if income it is a income cash amount else it is actual cash update
    income = models.BooleanField(default=False)

    db = models.ForeignKey(
        to=Database, on_delete=models.CASCADE, related_name='cashes')

    def __str__(self):
        return 'DT:{} {}€'.format(timezone.localtime(self.reference_date).strftime('%Y-%m'), self.value)

    def __repr__(self):
        return '<class Cash (for db {}): DT:{} {}€>'.format(self.db.name, timezone.localtime(self.reference_date).strftime('%Y-%m'), self.value)


class Category(models.Model):
    name = models.CharField(max_length=128)

    db = models.ForeignKey(
        to=Database, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return '{} - {}'.format(self.name, self.db.name)

    def __repr__(self):
        return '<class Category (for db {}): {}>'.format(self.db.name, self.name)


class Expenditure(models.Model):
    name = models.CharField(max_length=128)
    value = models.DecimalField(max_digits=11, decimal_places=2)
    date = models.DateTimeField(null=True)
    is_expected = models.BooleanField(default=False)

    category = models.ForeignKey(
        to=Category, on_delete=models.CASCADE, related_name='expenditures')
    user = models.ForeignKey(
        to=User, on_delete=models.CASCADE, related_name='expenditures')
    db = models.ForeignKey(
        to=Database, on_delete=models.CASCADE, related_name='expenditures')

    expected_expenditure = models.ForeignKey(
        to='self', null=True, on_delete=models.SET_NULL, related_name='actual_expenditures')

    def save(self, *args, **kwargs):
        self.db = self.category.db
        if not self.date:
            # must have a reference_date
            self.date = timezone.now()
        if self.is_expected:
            # this is a expected expenditure, can not have related expected expenditure
            self.expected_expenditure = None
        super(Expenditure, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<class Expenditure (for db {}): {} ({})>'.format(self.db.name,
                                                                 self.value,
                                                                 self.name)
