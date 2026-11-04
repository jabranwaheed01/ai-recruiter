
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import CallResult


SLOT_DURATION_MINUTES = 60


def _to_utc_naive(value: datetime) -> datetime:
    """Normalize datetime to UTC without timezone information."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    return value


def is_slot_available(
    db: Session,
    requested_datetime: datetime,
    exclude_call_id: int | None = None,
) -> bool:
    """Check whether a requested interview slot overlaps an existing booking."""

    requested_start = _to_utc_naive(requested_datetime)
    requested_end = requested_start + timedelta(
        minutes=SLOT_DURATION_MINUTES
    )

    query = (
        db.query(CallResult)
        .filter(
            CallResult.outcome == "Booked",
            CallResult.interview_datetime.isnot(None),
        )
    )

    # Allow the same candidate's existing booking to be checked again.
    if exclude_call_id is not None:
        query = query.filter(CallResult.call_id != exclude_call_id)

    booked_interviews = query.all()

    for booking in booked_interviews:
        booked_start = _to_utc_naive(booking.interview_datetime)
        booked_end = booked_start + timedelta(
            minutes=SLOT_DURATION_MINUTES
        )

        # Reject overlapping interview times.
        if (
            requested_start < booked_end
            and requested_end > booked_start
        ):
            return False

    return True


def check_interview_availability(
    db: Session,
    preferred_date: str | None = None,
) -> dict[str, Any]:
    """Return unbooked interview slots for the next seven days."""

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if preferred_date:
        try:
            selected_date = date.fromisoformat(preferred_date)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "preferred_date must use YYYY-MM-DD format."
            ) from exc
    else:
        selected_date = None

    available_slots = []

    for day_offset in range(1, 8):
        current_date = (now + timedelta(days=day_offset)).date()

        # Monday to Friday only.
        if current_date.weekday() >= 5:
            continue

        if selected_date and current_date != selected_date:
            continue

        for hour in [10, 11, 14, 15]:
            slot = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                hour,
                0,
            )

            if slot <= now:
                continue

            if is_slot_available(db, slot):
                available_slots.append({
                    "datetime": slot.isoformat() + "Z",
                    "timezone": "UTC",
                })

    return {
        "success": True,
        "available_slots": available_slots,
        "count": len(available_slots),
        "message": (
            "Available interview slots retrieved successfully."
            if available_slots
            else "No interview slots available for the requested date."
        ),
    }
