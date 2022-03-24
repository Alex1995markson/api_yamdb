from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return (
                    request.user.is_staff or
                    request.user.role == request.user.UserRole.ADMIN
            )
        return False


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.UserRole.ADMIN
            or request.method in permissions.SAFE_METHODS
        )


class IsAdminOrAuthorOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(request.method in permissions.SAFE_METHODS
                    or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.UserRole.MODERATOR
            or request.user.UserRole.ADMIN
        )


class ReadOnlyOrIsAdminOrModeratorOrAuthor(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            or request.method in permissions.SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return (
                request.user.UserRole.MODERATOR
                or request.user.UserRole.ADMIN
                or request.user == obj.author
            )
        return request.method in permissions.SAFE_METHODS
