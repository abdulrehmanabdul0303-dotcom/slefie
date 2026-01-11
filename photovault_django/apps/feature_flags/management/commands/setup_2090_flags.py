"""
Management command to set up PhotoVault 2090 feature flags.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.feature_flags.models import FeatureFlag, PHOTOVAULT_2090_FEATURES

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up PhotoVault 2090 feature flags'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--environment',
            type=str,
            default='DEVELOPMENT',
            choices=['DEVELOPMENT', 'STAGING', 'PRODUCTION'],
            help='Environment to enable flags in'
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable flags after creation'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            help='Admin user email for created_by field'
        )
        parser.add_argument(
            '--tags',
            nargs='+',
            help='Only create flags with these tags'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
    
    def handle(self, *args, **options):
        environment = options['environment']
        enable_flags = options['enable']
        admin_email = options['admin_email']
        tags_filter = options['tags']
        dry_run = options['dry_run']
        
        # Get admin user
        admin_user = None
        if admin_email:
            try:
                admin_user = User.objects.get(email=admin_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Admin user {admin_email} not found')
                )
        
        created_count = 0
        updated_count = 0
        
        self.stdout.write(f'Setting up PhotoVault 2090 feature flags...')
        self.stdout.write(f'Environment: {environment}')
        self.stdout.write(f'Enable flags: {enable_flags}')
        self.stdout.write(f'Tags filter: {tags_filter or "None"}')
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write('')
        
        for key, config in PHOTOVAULT_2090_FEATURES.items():
            # Filter by tags if specified
            if tags_filter and not any(tag in config['tags'] for tag in tags_filter):
                continue
            
            if dry_run:
                self.stdout.write(f'Would create/update: {key} - {config["name"]}')
                continue
            
            flag, created = FeatureFlag.objects.get_or_create(
                key=key,
                defaults={
                    'name': config['name'],
                    'description': config['description'],
                    'flag_type': config['flag_type'],
                    'is_active': enable_flags,
                    'tags': config['tags'],
                    'environments': [environment],
                    'created_by': admin_user,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {key} - {config["name"]}')
                )
            else:
                # Update existing flag
                updated = False
                
                if environment not in flag.environments:
                    flag.environments.append(environment)
                    updated = True
                
                if enable_flags and not flag.is_active:
                    flag.is_active = True
                    updated = True
                
                if updated:
                    flag.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated: {key} - {config["name"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(f'- Exists: {key} - {config["name"]}')
                    )
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Dry run completed. No changes made.'))
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Setup completed: {created_count} created, {updated_count} updated'
                )
            )
            
            if created_count > 0 or updated_count > 0:
                self.stdout.write('')
                self.stdout.write('Next steps:')
                self.stdout.write('1. Run migrations: python manage.py migrate')
                self.stdout.write('2. Check admin panel: /admin/feature_flags/')
                self.stdout.write('3. Test flags: /api/feature-flags/2090/')
                
                if not enable_flags:
                    self.stdout.write('')
                    self.stdout.write(
                        self.style.WARNING(
                            'Flags created but not enabled. Enable them in admin or use --enable flag.'
                        )
                    )