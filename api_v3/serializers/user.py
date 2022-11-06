from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .SimpleDatabaseSerializer import SimpleDatabaseSerializer


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
        ]


class PrivateUserSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=16, write_only=True)

    dbs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'date_joined',
            'last_login',
            'dbs',
        ]

    def validate_password(self, value):
        if self.context['request'].method == 'POST':
            validate_password(value)
        elif self.context['request'].method in ['PATCH', 'PUT'] and value is not None:
            validate_password(value)

    def _hash_password(self, attrs):
        attrs['password'] = make_password(attrs['password'])

    def validate(self, attrs):
        if self.context['request'].method == 'POST' or (
            self.context['request'].method in ['PATCH', 'PUT'] and 'password' in attrs
        ):
            self._hash_password(attrs)

        return super().validate(attrs)

    def to_representation(self, instance):
        if self.context['request'].method == 'POST':
            Token.objects.get_or_create(user=instance)
            return {'id': instance.id, 'auth_token': instance.auth_token.key}
        return super().to_representation(instance)
