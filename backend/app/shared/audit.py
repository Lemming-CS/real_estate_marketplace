from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import AdminAuditLog, User


def record_admin_audit_log(
    session: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    description: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    before_json: dict | list | None = None,
    after_json: dict | list | None = None,
    metadata_json: dict | list | None = None,
) -> None:
    session.add(
        AdminAuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )
    )
