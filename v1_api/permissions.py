from rest_framework import permissions


class UserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        print('user', request.user)
        return obj.id == request.user.id


class DBPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        print('user', request.user)
        # only users in dbs users can do actions on that DB, also view it is denied
        return obj.users.filter(id=request.user.id).exists()


class DBRelatedPermission(permissions.BasePermission):
    # I created a generic class and not a specific one for every model class because authorization is the same
    def has_object_permission(self, request, view, obj):
        print('user', request.user)
        # only users in dbs users can do actions on cash
        return obj.db.users.filter(id=request.user.id).exists()


'''
class CashPermission(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		# only users in dbs users can do actions on cash
		return obj.db.users.filter(id=request.user.id).exists()

class CategoryPermission(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		# only users in dbs users can do actions on cash
		return obj.db.users.filter(id=request.user.id).exists()

class ExpenditurePermission(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		# only users in dbs users can do actions on cash
		return obj.db.users.filter(id=request.user.id).exists()
'''
