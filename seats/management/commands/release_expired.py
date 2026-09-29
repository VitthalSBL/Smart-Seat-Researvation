from django.core.management.base import BaseCommand
from seats.services import release_expired


class Command(BaseCommand):
    help = "Expired holds release karo (optional cron; API calls bhi ye khud karti hain)"

    def handle(self, *a, **kw):
        self.stdout.write(f"Released: {release_expired()}")
