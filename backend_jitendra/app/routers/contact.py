"""Homepage contact form, replacing the localStorage write in js/contact.js."""

from __future__ import annotations

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from ..deps import CurrentUser, DbSession
from ..models import ContactMessage
from ..schemas import ContactAck, ContactMessageOut, ContactRequest

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", response_model=ContactAck, status_code=status.HTTP_201_CREATED)
def submit_message(payload: ContactRequest, db: DbSession) -> ContactAck:
    entry = ContactMessage(
        name=payload.name,
        mobile=payload.mobile,
        email=payload.email.strip().lower(),
        message=(payload.message or "").strip() or None,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return ContactAck(
        id=entry.id,
        message=f"Thanks, {entry.name}! We've received your message and will get back to you soon.",
        created_at=entry.created_at,
    )


@router.get("", response_model=list[ContactMessageOut])
def list_messages(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ContactMessage]:
    """Inbox view. Authenticated because submissions contain personal details."""

    return list(
        db.scalars(
            select(ContactMessage)
            .order_by(ContactMessage.created_at.desc(), ContactMessage.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
