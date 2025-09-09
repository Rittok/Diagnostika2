from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count

class Command(BaseCommand):
    help = 'Remove duplicate users based on email.'

    def handle(self, *args, **options):
        duplicates = (
            User.objects.values('email')
            .annotate(email_count=Count('email'))
            .filter(email_count__gt=1)
        )

        for duplicate in duplicates:
            emails = duplicate['email']
            users = User.objects.filter(email=emails)
            keep_user = users.first()
            delete_users = users.exclude(pk=keep_user.pk)
            delete_users.delete()

        self.stdout.write(self.style.SUCCESS('Successfully removed duplicate users.'))