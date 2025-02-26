from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
import json
import logging

from main.models import Database, Cash, Category, Expenditure
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from .exceptions import NotAllowedAction
from .permissions import DBPermission, DBRelatedPermission, UserPermission
from .serializers import (
    PrivateUserSerializer,
    PublicUserSerializer,
    CategorySerializer,
    FullDatabaseSerializer,
    GraphDatabaseSerializer,
    SimpleDatabaseSerializer,
    CashSerializer,
    ExpenditureSerializer,
)

logger = logging.getLogger(__name__)


def render_version(request):
    try:
        with open(settings.VERSION_FILE, "r") as f:
            v = json.load(f)
    except Exception as e:
        v = "unknown"
    return JsonResponse({"api_version": "v3", "version": str(v)})


class ExtendedAuthToken(ObtainAuthToken):
    def _not_authenticated(self):
        r = JsonResponse({"detail": "Invalid or missing token."})
        r.status_code = 401
        return r

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return JsonResponse(
                PrivateUserSerializer(context={"request": request}).to_representation(
                    request.user
                )
            )
        return self._not_authenticated()

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        request.user = user
        Token.objects.get_or_create(user=user)
        return JsonResponse(
            PrivateUserSerializer(context={"request": request}).to_representation(
                request.user
            )
        )


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [UserPermission]
    paginator = None

    def get_queryset(self):
        ids = self.request.params.get("ids", None)
        if ids is not None:
            return User.objects.filter(
                id__in=ids[0].strip().lower().split(",")
            ).order_by("id")
        return User.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PrivateUserSerializer
        return PublicUserSerializer


class UserSearchViewSet(viewsets.ModelViewSet):
    permission_classes = [UserPermission]
    http_method_names = ["options", "head", "get"]
    model = User
    serializer_class = PublicUserSerializer
    paginator = None

    def get_queryset(self):
        """
        Available parameters are username
        """
        username = self.request.params.get("username", None)
        if username is None:
            return User.objects.none()
        return User.objects.filter(
            username__icontains=username[0].strip().lower()
        ).order_by("username")


class DBRelatedViewSet(viewsets.ModelViewSet):
    permission_classes = [DBRelatedPermission]
    http_method_names = ["options", "head", "get", "post", "patch", "update", "delete"]

    def _attach_db(self):
        db_id = self.request.params.get("db", [self.request.headers.get("db", None)])[0]
        if db_id:
            dbs = Database.objects.filter(users__in=[self.request.user], id=db_id)
            if not dbs.count():
                raise Http404
            self.request.db = dbs.first()

    def initial(self, request, *args, **kwargs):
        ret = super().initial(request, *args, **kwargs)
        self._attach_db()
        return ret

    def get_queryset(self):
        return self.model.objects.filter(db__users__in=[self.request.user])


class ModelViewSet(viewsets.ModelViewSet):
    paginator = None

    def get_queryset(self):
        # First call DBRelated.get_queryset that also provide self.request.db if available
        queryset = super().get_queryset()

        method = self.request.method
        if method == "GET":
            is_list = not self.kwargs.get("pk", False)
            # if is_list we need to limit the queryset
            if is_list:
                ids = self.request.params.get("id", [])
                if ids:
                    queryset = queryset.filter(id__in=ids)
                # If id are not provided try to limit queryset by fetching only object related to db found in headers or parameters
                elif hasattr(self.request, "db"):
                    queryset = queryset.filter(db=self.request.db)
                else:
                    # Raise not allowed action if list is not limited by one or multiple id in params or database found in headers or parameters
                    raise NotAllowedAction("list")
        return queryset


class DatabaseDBRelatedAdapter(DBRelatedViewSet):
    def get_queryset(self):
        return self.model.objects.filter(users__in=[self.request.user])


class DatabaseViewSet(
    ModelViewSet,
    DatabaseDBRelatedAdapter,
):
    model = Database
    serializer_class = FullDatabaseSerializer
    permission_classes = [DBPermission]

    def get_serializer_class(self):
        method = self.request.method
        is_list = not self.kwargs.get("pk", False)
        if method == "GET" and is_list:
            return SimpleDatabaseSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        methods=["get", "head", "options"],
        serializer_class=GraphDatabaseSerializer,
    )
    def graph(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CashViewSet(ModelViewSet, DBRelatedViewSet):
    model = Cash
    serializer_class = CashSerializer


class CategoryViewSet(ModelViewSet, DBRelatedViewSet):
    model = Category
    serializer_class = CategorySerializer


class ExpenditureViewSet(ModelViewSet, DBRelatedViewSet):
    model = Expenditure
    serializer_class = ExpenditureSerializer

    def get_serializer(self, *args, **kwargs):
        if "many" not in kwargs:
            data = kwargs.get("data", None)
            if data:
                kwargs["many"] = isinstance(data, list)
        return super().get_serializer(*args, **kwargs)


class ExpenditureSearchViewSet(DBRelatedViewSet):
    http_method_names = ["options", "head", "get"]
    model = Expenditure
    serializer_class = ExpenditureSerializer
    paginator = None

    def _queryset_from_queryString(self, queryset):
        query_string = self.request.params.get("queryString", None)
        if query_string is None:
            return queryset
        query_string = query_string[0]
        queries = [
            [Q(name__icontains=AND) for AND in OR.strip().split(" ")]
            for OR in query_string.split(",")
        ]
        ORS = []
        for qs in queries:
            query = qs[0]
            for i in range(1, len(qs)):
                query = query & qs[i]
            ORS.append(query)
        query = ORS[0]
        for i in range(1, len(ORS)):
            query = query | ORS[i]

        return queryset.filter(query)

    def get_queryset(self):
        """
        Available parameters are queryString, from, to, lowerPrice, upperPrice, type ['both', 'actual', 'expected']
        """
        other_parameters = False
        query = Q(db__in=self.request.user.dbs.all())
        for key, value in self.request.params.items():
            if key == "from":
                other_parameters = True
                query = query & Q(date__gte=value[0])
            elif key == "to":
                other_parameters = True
                query = query & Q(date__lte=value[0])
            elif key == "lowerPrice":
                other_parameters = True
                query = query & Q(value__gte=value[0])
            elif key == "upperPrice":
                other_parameters = True
                query = query & Q(value__lte=value[0])
            elif key == "type":
                if value[0] == "actual":
                    other_parameters = True
                    query = query & Q(is_expected=False)
                elif value[0] == "expected":
                    other_parameters = True
                    query = query & Q(is_expected=True)
        if other_parameters or len(self.request.params.get("queryString", [])) > 0:
            queryset = Expenditure.objects.filter(query)
            queryset = self._queryset_from_queryString(queryset)
            return queryset.order_by("-date")
        return Expenditure.objects.none()
