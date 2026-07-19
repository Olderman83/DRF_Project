from rest_framework import permissions

class IsModerator(permissions.BasePermission):
    """
    Проверяет, является ли пользователь модератором
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='moderators').exists()

class IsOwner(permissions.BasePermission):
    """
    Проверяет, является ли пользователь владельцем объекта
    """
    def has_object_permission(self, request, view, obj):
        # Проверяем, есть ли у объекта поле owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False

class IsOwnerOrModerator(permissions.BasePermission):
    """
    Разрешает доступ владельцу объекта или модератору
    """
    def has_object_permission(self, request, view, obj):
        if request.user.groups.filter(name='moderators').exists():
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает просмотр всем, изменение только владельцу
    """
    def has_object_permission(self, request, view, obj):
        # Разрешаем просмотр всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Изменение только владельцу
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False
