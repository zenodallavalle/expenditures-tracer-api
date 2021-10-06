from rest_framework import serializers

from main.models import Database


class SimpleDatabaseSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def __init__(self, *args, include_children=False, **kwargs):
        self.include_children = include_children
        super().__init__(*args, **kwargs)

    class Meta:
        model = Database
        fields = ['id', 'name', 'users']
