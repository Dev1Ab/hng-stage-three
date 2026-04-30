from rest_framework import permissions
    
class IsAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser)
        )
    
class IsActiveUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active
