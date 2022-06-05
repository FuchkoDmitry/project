from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        permission = request.user == obj.creator
        if request.user.is_staff or request.user.is_superuser:
            return True

        return permission
