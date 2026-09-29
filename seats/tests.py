import threading
from datetime import timedelta
from unittest import skipUnless

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from .models import Seat
from .services import SeatError, confirm_payment, release_expired, set_selection


def make_seats():
    return [Seat.objects.create(label=f"A{i}", row="A", number=i) for i in range(1, 6)]


class ReservationTests(TestCase):
    def setUp(self):
        self.s = make_seats()
        self.u1 = User.objects.create_user("u1", password="x")
        self.u2 = User.objects.create_user("u2", password="x")

    def test_reserve_multiple_and_block_others(self):
        set_selection(self.u1, [self.s[0].id, self.s[1].id])
        with self.assertRaises(SeatError):
            set_selection(self.u2, [self.s[1].id, self.s[2].id])
        self.s[2].refresh_from_db()
        self.assertEqual(self.s[2].status, Seat.AVAILABLE)  # rollback hua

    def test_modify_selection(self):
        set_selection(self.u1, [self.s[0].id, self.s[1].id])
        set_selection(self.u1, [self.s[1].id, self.s[2].id])
        self.s[0].refresh_from_db()
        self.assertEqual(self.s[0].status, Seat.AVAILABLE)
        set_selection(self.u2, [self.s[0].id])  # ab u2 le sakta hai

    def test_expiry_releases_seat(self):
        set_selection(self.u1, [self.s[0].id])
        Seat.objects.update(reserved_until=timezone.now() - timedelta(seconds=1))
        release_expired()
        set_selection(self.u2, [self.s[0].id])

    def test_pay_after_expiry_fails(self):
        set_selection(self.u1, [self.s[0].id])
        Seat.objects.update(reserved_until=timezone.now() - timedelta(seconds=1))
        with self.assertRaises(SeatError):
            confirm_payment(self.u1)

    def test_booked_cannot_be_taken(self):
        set_selection(self.u1, [self.s[0].id]); confirm_payment(self.u1)
        with self.assertRaises(SeatError):
            set_selection(self.u2, [self.s[0].id])


@skipUnless(connection.vendor == "postgresql", "Real concurrency test PostgreSQL pe chalta hai")
class ConcurrencyTest(TransactionTestCase):
    def test_no_double_booking(self):
        seat = make_seats()[0]
        users = [User.objects.create_user(f"c{i}", password="x") for i in range(20)]
        results = []

        def worker(u):
            try:
                set_selection(u, [seat.id]); results.append("ok")
            except SeatError:
                results.append("fail")
            finally:
                connection.close()

        ts = [threading.Thread(target=worker, args=(u,)) for u in users]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(results.count("ok"), 1)
