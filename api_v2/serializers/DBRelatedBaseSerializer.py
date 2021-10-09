from rest_framework import serializers

from .FullDatabaseSerializer import FullDatabaseSerializer


class DBRelatedBaseSerializer(serializers.ModelSerializer):
    def represent_db(self, db):
        representation = FullDatabaseSerializer(
            db, context=self.context, include_children=True).to_representation(db)
        return representation

    def to_representation(self, instance):
        db = instance.db
        return self.represent_db(db)

    def destroy(self, instance):
        instance.delete()
        return self.represent_db(instance.db)
