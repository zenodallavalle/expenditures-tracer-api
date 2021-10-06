from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .SimpleDatabaseSerializer import SimpleDatabaseSerializer


class PublicUserSerializer(serializers.ModelSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['id', 'username', ]


class PrivateUserSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)

    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=16, write_only=True)

    dbs = SimpleDatabaseSerializer(many=True, read_only=True)

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name',
                  'email', 'password', 'date_joined', 'last_login',
                  'dbs', ]

    def _validate_and_hash_password(self, attrs):
        validate_password(attrs['password'])
        attrs['password'] = make_password(attrs['password'])

    def validate(self, attrs):
        if self.context['request'].method == 'POST':
            self._validate_and_hash_password(attrs)
        elif self.context['request'].method in ['PATCH', 'PUT'] and 'password' in attrs:
            self._validate_and_hash_password(attrs)

        return super().validate(attrs)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['request'].method == 'POST':
            representation['auth_token'] = instance.auth_token.key
        return representation
