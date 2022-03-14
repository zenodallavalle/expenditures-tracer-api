from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .SimpleDatabaseSerializer import SimpleDatabaseSerializer


class PublicUserSerializer(serializers.ModelSerializer):
    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    # email = serializers.EmailField(write_only=True, required=True)
    # password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
        ]

    # def create(self, validated_data):
    #     password = validated_data.pop('password')
    #     user = super().create(validated_data)
    #     user.set_password(password)
    #     print(user)
    #     print(user.__dict__)
    #     return user


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
            self._hash_password(attrs['password'])

        return super().validate(attrs)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['request'].method == 'POST':
            Token.objects.get_or_create(user=instance)
            representation['auth_token'] = instance.auth_token.key
        return representation
