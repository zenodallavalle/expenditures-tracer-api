from rest_framework import permissions


class DBPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and obj.users.filter(id=request.user.id).exists()


class DBRelatedPermission(permissions.IsAuthenticated):
    # I created a generic class and not a specific one for every model class because authorization is the same
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and obj.db.users.filter(id=request.user.id).exists()