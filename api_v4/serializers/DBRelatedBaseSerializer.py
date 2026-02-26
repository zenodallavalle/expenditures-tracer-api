from rest_framework import serializers

from main.models import Database


class ForeignToDBField(serializers.PrimaryKeyRelatedField):
    class Meta:
        model = Database

    def get_queryset(self):
        user = self.context['request'].user
        return Database.objects.filter(users__in=[user])


class DBRelatedBaseSerializer(serializers.ModelSerializer):

    db = ForeignToDBField(required=False)

    def validate_db(self, value):
        if not value:
            if not self.context['request'].get('db', None):
                raise serializers.ValidationError(
                    "db must be specified either in request's body or in headers"
                )
            if self.instance and self.instance.db != self.context['request']['db']:
                raise serializers.ValidationError('You may not edit db.')
        else:
            if self.instance and self.instance.db != value:
                raise serializers.ValidationError('You may not edit db.')

    def validate(self, attrs):
        if not attrs.get('db', None):
            attrs['db'] = getattr(self.context['request'], 'db', None)
        if self.context['request'].method in ['PATCH', 'PUT']:
            del attrs['db']
        return super().validate(attrs)
