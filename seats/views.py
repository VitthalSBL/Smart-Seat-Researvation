import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from . import services
from .models import Seat


@login_required
@ensure_csrf_cookie
def index(request):
    return render(request, "seats/index.html")


@login_required
@require_GET
def api_seats(request):
    now = timezone.now()
    services.release_expired(now)
    seats, my_deadline = [], None
    for s in Seat.objects.all():
        if s.status == Seat.RESERVED and s.reserved_by_id == request.user.id:
            state = "mine"
            if my_deadline is None or s.reserved_until < my_deadline:
                my_deadline = s.reserved_until
        else:
            state = s.status
        seats.append({"id": s.id, "label": s.label, "row": s.row, "state": state})
    remaining = max(0, int((my_deadline - now).total_seconds())) if my_deadline else None
    return JsonResponse({"seats": seats, "expires_in": remaining})


def _body_ids(request):
    try:
        return [int(i) for i in json.loads(request.body or b"{}").get("seat_ids", [])]
    except (ValueError, TypeError):
        raise services.SeatError("Bad request.")


@login_required
@require_POST
def api_select(request):
    try:
        labels = services.set_selection(request.user, _body_ids(request))
    except services.SeatError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=409)
    return JsonResponse({"ok": True, "reserved": labels})


@login_required
@require_POST
def api_pay(request):
    try:
        labels = services.confirm_payment(request.user)
    except services.SeatError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=409)
    return JsonResponse({"ok": True, "booked": labels})
