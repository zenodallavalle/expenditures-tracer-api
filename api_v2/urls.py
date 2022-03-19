"""expendituresTracer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'dbs', views.DatabaseViewSet, basename='dbs')
router.register(r'cash', views.CashViewSet, basename='cashes')
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'expenditures', views.ExpenditureViewSet, basename='expenditures')

urlpatterns = [
    path('months/', views.get_months, name='months'),
    path(
        'copy-expenditures-from-precedent-month/',
        views.copy_from_precedent_month,
        name='copy-from-precedent-month',
    ),
    path(
        'expenditures/search/',
        views.ExpenditureSearchViewSet.as_view({'get': 'list'}),
        name='search expenditures',
    ),
    path(
        'users/search/',
        views.UserSearchViewSet.as_view({'get': 'list'}),
        name='searc users',
    ),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', views.ExtendedAuthToken.as_view(), name='api_token_auth'),
    path('', include(router.urls)),
]
