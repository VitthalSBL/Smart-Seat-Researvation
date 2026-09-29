"""Saari booking logic yahin hai. Har state-change transaction.atomic + row locks ke andar."""
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import HOLD_SECONDS, Seat

MAX_SEATS_PER_USER = 8


class SeatError(Exception):
    pass


def release_expired(now=None):
    """2 minute se purani holds ko automatically free kar do."""
    now = now or timezone.now()
    return Seat.objects.filter(status=Seat.RESERVED, reserved_until__lte=now).update(
        status=Seat.AVAILABLE, reserved_by=None, reserved_until=None)


@transaction.atomic
def set_selection(user, seat_ids):
    """User ki poori selection ko `seat_ids` set se replace karta hai (add + remove ek saath).
    Agar koi bhi seat conflict kare to poora transaction rollback -> purani selection safe rehti hai."""
    seat_ids = set(seat_ids)
    if len(seat_ids) > MAX_SEATS_PER_USER:
        raise SeatError(f"Maximum {MAX_SEATS_PER_USER} seats hi select kar sakte hain.")

    now = timezone.now()
    release_expired(now)

    # Requested seats + user ki current holds ko lock karo. order_by('id') => deadlock nahi hoga.
    locked = list(
        Seat.objects.select_for_update()
        .filter(Q(id__in=seat_ids) | Q(status=Seat.RESERVED, reserved_by=user))
        .order_by("id")
    )
    if not seat_ids <= {s.id for s in locked}:
        raise SeatError("Invalid seat selected.")

    conflicts, to_save = [], []
    for seat in locked:
        wanted = seat.id in seat_ids
        mine = seat.status == Seat.RESERVED and seat.reserved_by_id == user.id
        if wanted:
            if seat.status == Seat.BOOKED or (seat.status == Seat.RESERVED and not mine):
                conflicts.append(seat.label)
            elif not mine:  # available -> naya 2 min hold
                seat.status = Seat.RESERVED
                seat.reserved_by = user
                seat.reserved_until = now + timedelta(seconds=HOLD_SECONDS)
                to_save.append(seat)
            # mine -> purana deadline wahi rehne do (timer reset karke infinite hold nahi ban sakta)
        elif mine:  # user ne deselect kiya -> release
            seat.status, seat.reserved_by, seat.reserved_until = Seat.AVAILABLE, None, None
            to_save.append(seat)

    if conflicts:
        raise SeatError("Ye seats ab available nahi hain: " + ", ".join(sorted(conflicts)))

    Seat.objects.bulk_update(to_save, ["status", "reserved_by", "reserved_until"])
    return list(Seat.objects.filter(status=Seat.RESERVED, reserved_by=user).values_list("label", flat=True))


@transaction.atomic
def confirm_payment(user):
    """Payment success maan kar held seats ko BOOKED bana do (real project me gateway callback yahan aayega)."""
    now = timezone.now()
    release_expired(now)
    seats = list(Seat.objects.select_for_update()
                 .filter(status=Seat.RESERVED, reserved_by=user, reserved_until__gt=now)
                 .order_by("id"))
    if not seats:
        raise SeatError("Koi active reservation nahi hai (time expire ho gaya ho sakta hai).")
    for s in seats:
        s.status, s.booked_by, s.booked_at = Seat.BOOKED, user, now
        s.reserved_by = s.reserved_until = None
    Seat.objects.bulk_update(seats, ["status", "booked_by", "booked_at", "reserved_by", "reserved_until"])
    return [s.label for s in seats]
