from django.core.management.base import BaseCommand
from django.conf import settings
import datetime
from bson import ObjectId

class Command(BaseCommand):
    help = 'Set up initial data for the application'
    
    def handle(self, *args, **options):
        # Check MongoDB connection - use the correct way to check if DB is None
        if not hasattr(settings, 'MONGODB_DB') or settings.MONGODB_DB is None:
            self.stdout.write(self.style.ERROR('MongoDB client not configured in settings'))
            return
           
        try:
            # Create default organization if it doesn't exist
            organizations_collection = settings.MONGODB_DB['organizations']
            default_org = organizations_collection.find_one({'name': 'Default Organization'})
           
            if not default_org:
                org_data = {
                    '_id': ObjectId("000000000000000000000001"),
                    'name': 'Default Organization',
                    'description': 'Default organization for all users',
                    'created_at': datetime.datetime.now()
                }
                organizations_collection.insert_one(org_data)
                self.stdout.write(self.style.SUCCESS('Created default organization'))
                org_id = org_data['_id']
            else:
                org_id = default_org['_id']
                self.stdout.write('Default organization already exists')
           
            # Create default roles if they don't exist
            roles_collection = settings.MONGODB_DB['roles']
           
            roles = [
                {
                    'name': 'admin',
                    'description': 'Administrator with full permissions',
                    'permission_level': 4
                },
                {
                    'name': 'manager',
                    'description': 'Manager with team management permissions',
                    'permission_level': 3
                },
                {
                    'name': 'team_member',
                    'description': 'Regular team member',
                    'permission_level': 1
                }
            ]
           
            for role_data in roles:
                existing_role = roles_collection.find_one({'name': role_data['name']})
                if not existing_role:
                    roles_collection.insert_one(role_data)
                    self.stdout.write(self.style.SUCCESS(f"Created {role_data['name']} role"))
                else:
                    self.stdout.write(f"{role_data['name']} role already exists")
                   
            # Create default team if it doesn't exist
            teams_collection = settings.MONGODB_DB['teams']
            default_team = teams_collection.find_one({'name': 'General'})
           
            if not default_team:
                team_data = {
                    'name': 'General',
                    'description': 'General team for all users',
                    'organization': org_id,
                    'members': [],
                    'created_at': datetime.datetime.now()
                }
                teams_collection.insert_one(team_data)
                self.stdout.write(self.style.SUCCESS('Created default team'))
            else:
                self.stdout.write('Default team already exists')
               
            self.stdout.write(self.style.SUCCESS('Initial setup completed successfully'))
           
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during initial setup: {e}"))