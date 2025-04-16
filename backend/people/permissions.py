from rest_framework import permissions


class IsAdminOrManager(permissions.BasePermission):
    """
    Custom permission to only allow admins or managers to access/modify.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_admin() or request.user.is_manager()
        )


class IsTeamLeader(permissions.BasePermission):
    """
    Custom permission to only allow team leaders to access/modify their teams.
    """
    def has_object_permission(self, request, view, obj):
        # obj could be a Team
        if hasattr(obj, 'leader'):
            return request.user == obj.leader
            
        # obj could be something with a team attribute
        if hasattr(obj, 'team') and obj.team:
            return request.user == obj.team.leader
            
        return False


class IsTaskModifier(permissions.BasePermission):
    """
    Custom permission to check if a user can modify a task.
    """
    def has_object_permission(self, request, view, obj):
        # Call the can_user_modify method from the Task model
        return obj.can_user_modify(request.user)


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to modify their own data
    or admins/managers to modify any user data.
    """
    def has_object_permission(self, request, view, obj):
        # obj is a User instance
        return (
            request.user == obj or 
            request.user.is_admin() or 
            request.user.is_manager()
        )
