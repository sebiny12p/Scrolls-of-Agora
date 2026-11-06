"""
Mailbox & Courier Parcel API Router for Scrolls of Agora.
Handles asynchronous item delivery, gold attachments, and Cash-on-Delivery (COD).
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from src.models import MailSendRequest, MailClaimRequest
from src.repositories.mail_repo import (
    get_player_mailbox,
    send_player_mail,
    claim_mail_attachment,
)
from src.auth import get_current_player_id, resolve_effective_player_id

router = APIRouter(prefix="/api/mail", tags=["Mailbox"])


@router.get("")
def api_get_mailbox(
    player_id: Optional[int] = Query(None, description="Player ID to view mailbox"),
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    pid = resolve_effective_player_id(player_id or 1005, auth_pid)
    mail_items = get_player_mailbox(pid)
    return {
        "success": True,
        "player_id": pid,
        "mail_count": len(mail_items),
        "uncollected_count": sum(1 for m in mail_items if not m["is_collected"]),
        "mailbox": mail_items,
    }


@router.post("/send")
def api_send_mail(
    req: MailSendRequest,
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    sender_id = resolve_effective_player_id(req.sender_id, auth_pid)
    return send_player_mail(
        sender_id=sender_id,
        recipient_id=req.recipient_id,
        subject=req.subject,
        body=req.body,
        attached_gold=req.attached_gold,
        attached_instance_id=req.attached_instance_id,
        cod_amount=req.cod_amount,
    )


@router.post("/claim")
def api_claim_mail(
    req: MailClaimRequest,
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    player_id = resolve_effective_player_id(req.player_id, auth_pid)
    return claim_mail_attachment(mail_id=req.mail_id, player_id=player_id)
