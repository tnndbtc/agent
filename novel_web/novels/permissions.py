"""Custom permissions for novels app."""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Permission to only allow owners of an object to view/edit it."""

    def has_object_permission(self, request, view, obj):
        # Check if obj has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Check if obj has a project with a user
        elif hasattr(obj, 'project'):
            return obj.project.user == request.user
        return False
