from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from seats.models import Seat


class Command(BaseCommand):
    help = "Demo seats (A-F x 10) aur users (user1..user3 / test1234) banata hai"

    def handle(self, *a, **kw):
        for r in "ABCDEF":
            for n in range(1, 11):
                Seat.objects.get_or_create(label=f"{r}{n}", defaults={"row": r, "number": n})
        for i in (1, 2, 3):
            if not User.objects.filter(username=f"user{i}").exists():
                User.objects.create_user(f"user{i}", password="test1234")
        self.stdout.write(self.style.SUCCESS("Seeded."))
