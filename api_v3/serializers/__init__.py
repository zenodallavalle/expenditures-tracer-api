from django.conf import settings
from .SimpleDatabaseSerializer import SimpleDatabaseSerializer
from .FullDatabaseSerializer import FullDatabaseSerializer


from .user import PrivateUserSerializer, PublicUserSerializer


from .DBRelatedBaseSerializer import DBRelatedBaseSerializer
from .category import CategorySerializer as CTGRS
from .cash import CashSerializer as CSHS
from .expenditure import ExpenditureSerializer as EXPNDTRS


class CategorySerializer(CTGRS):
    pass


class CashSerializer(CSHS):
    pass


class ExpenditureSerializer(EXPNDTRS):
    pass
