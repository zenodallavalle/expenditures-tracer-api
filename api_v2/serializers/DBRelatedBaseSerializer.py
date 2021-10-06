from rest_framework import serializers
import pprint

from .FullDatabaseSerializer import FullDatabaseSerializer
# Cannot do so, to avoid circular import, we have to redeclare FullDatabaseSerializer and all called Serializers


class DBRelatedBaseSerializer(serializers.ModelSerializer):
    def represent_db(self, db):
        print('to represent db', db)
        representation = FullDatabaseSerializer(
            db, context=self.context, include_children=True).to_representation(db)
        pprint.pprint(representation)
        return representation

    def to_representation(self, instance):
        db = instance.db
        print('to represent db', db)
        return self.represent_db(db)

    def create(self, validated_data):
        pprint.pprint(validated_data)
        return super().create(validated_data)

    def destroy(self, instance):
        print('destroy instance', instance, instance.id)
        instance.delete()
        return self.represent_db(instance.db)
