from rest_framework import serializers
from .models import User, Role, Team

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permission_level']


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'role_name', 'profile_picture', 'bio', 'date_joined']
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class TeamMemberSerializer(serializers.ModelSerializer):
    """Simplified User serializer for team member lists"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture']


class TeamSerializer(serializers.ModelSerializer):
    leader_details = TeamMemberSerializer(source='leader', read_only=True)
    members_details = TeamMemberSerializer(source='members', many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'leader', 'leader_details', 
                 'members', 'members_details', 'created_at']
        read_only_fields = ['created_at']