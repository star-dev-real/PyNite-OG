from sanic import Blueprint, json
from sanic.response import empty
import json as json_module
from pathlib import Path
import uuid
from datetime import datetime

bp = Blueprint("friends", url_prefix="/")

@bp.get("/friends/api/v1/<account_id:str>/settings")
async def get_friend_settings(request, account_id):
    return json({})

@bp.get("/friends/api/public/list/fortnite/<account_id:str>/recentPlayers")
async def get_recent_players(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/summary")
async def get_friend_summary(request, account_id):
    return json({
        "friends": [],
        "incoming": [],
        "outgoing": [],
        "suggested": [],
        "blocklist": [],
        "settings": {
            "acceptInvites": "public"
        }
    })

@bp.get("/friends/api/public/friends/<account_id:str>")
async def get_friends_list(request, account_id):
    return json([])

@bp.post("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>")
async def add_friend(request, account_id, friend_account_id):
    return json({
        "status": "PENDING"
    })

@bp.delete("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>")
async def remove_friend(request, account_id, friend_account_id):
    return empty(status=204)

@bp.post("/friends/api/v1/<account_id:str>/blocklist/<blocked_account_id:str>")
async def block_user(request, account_id, blocked_account_id):
    return json({
        "status": "BLOCKED"
    })

@bp.delete("/friends/api/v1/<account_id:str>/blocklist/<blocked_account_id:str>")
async def unblock_user(request, account_id, blocked_account_id):
    return empty(status=204)

@bp.get("/friends/api/v1/<account_id:str>/blocklist")
async def get_blocklist(request, account_id):
    return json([])

@bp.post("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>/alias")
async def set_friend_alias(request, account_id, friend_account_id):
    body = request.json if request.json else {}
    alias = body.get("alias", "")
    
    return json({
        "alias": alias
    })

@bp.delete("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>/alias")
async def remove_friend_alias(request, account_id, friend_account_id):
    return empty(status=204)

@bp.get("/friends/api/v1/<account_id:str>/incoming")
async def get_incoming_requests(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/outgoing")
async def get_outgoing_requests(request, account_id):
    return json([])

@bp.post("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>/note")
async def set_friend_note(request, account_id, friend_account_id):
    body = request.json if request.json else {}
    note = body.get("note", "")
    
    return json({
        "note": note
    })

@bp.get("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>")
async def get_friend_status(request, account_id, friend_account_id):
    return json({
        "accountId": friend_account_id,
        "status": "PENDING",
        "direction": "OUTBOUND",
        "created": datetime.utcnow().isoformat() + "Z",
        "favorite": False
    })

@bp.get("/friends/api/v1/<account_id:str>/recent/fortnite")
async def get_recent_fortnite_players(request, account_id):
    return json([])

@bp.get("/friends/api/public/blocklist/<account_id:str>")
async def get_public_blocklist(request, account_id):
    return json({
        "blockedUsers": []
    })

@bp.get("/friends/api/v1/<account_id:str>/friends")
async def get_friends_v1(request, account_id):
    return json([])

@bp.post("/friends/api/v1/<account_id:str>/friends/bulk/delete")
async def bulk_delete_friends(request, account_id):
    return empty(status=204)

@bp.post("/friends/api/v1/<account_id:str>/friends/bulk/block")
async def bulk_block_friends(request, account_id):
    return empty(status=204)

@bp.get("/friends/api/v1/<account_id:str>/suggested")
async def get_suggested_friends(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/count")
async def get_friend_count(request, account_id):
    return json({
        "count": 0
    })

@bp.get("/friends/api/v1/<account_id:str>/friends/import")
async def get_friend_import_status(request, account_id):
    return json({
        "importable": [],
        "imported": []
    })

@bp.post("/friends/api/v1/<account_id:str>/friends/import")
async def import_friends(request, account_id):
    return json({
        "imported": []
    })

@bp.get("/friends/api/v1/<account_id:str>/friends/sync")
async def sync_friends(request, account_id):
    return json({
        "added": [],
        "removed": []
    })

@bp.get("/friends/api/v1/<account_id:str>/friends/availability")
async def get_friends_availability(request, account_id):
    return json({
        "available": True
    })

@bp.get("/friends/api/v1/<account_id:str>/friends/recommendations")
async def get_friend_recommendations(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/search")
async def search_friends(request, account_id):
    query = request.args.get("query", "")
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/fortnite")
async def get_fortnite_friends(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/summary")
async def get_friends_summary(request, account_id):
    return json({
        "friends": [],
        "incoming": [],
        "outgoing": [],
        "blocklist": []
    })

@bp.post("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>/accept")
async def accept_friend_request(request, account_id, friend_account_id):
    return json({
        "status": "ACCEPTED"
    })

@bp.post("/friends/api/v1/<account_id:str>/friends/<friend_account_id:str>/reject")
async def reject_friend_request(request, account_id, friend_account_id):
    return empty(status=204)

@bp.get("/friends/api/v1/<account_id:str>/presence")
async def get_friends_presence(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/fortnite/online")
async def get_online_fortnite_friends(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/fortnite/offline")
async def get_offline_fortnite_friends(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/fortnite/away")
async def get_away_fortnite_friends(request, account_id):
    return json([])

@bp.get("/friends/api/v1/<account_id:str>/friends/fortnite/busy")
async def get_busy_fortnite_friends(request, account_id):
    return json([])

@bp.get("/api/v1/contacts/friends/<account_id:str>")
async def get_contacts_friends(request, account_id):
    return json([])

@bp.get("/api/v1/contacts/friends/<account_id:str>/presence")
async def get_contacts_presence(request, account_id):
    return json([])

@bp.post("/api/v1/contacts/friends/<account_id:str>/invites")
async def send_contact_invite(request, account_id):
    body = request.json if request.json else {}
    return json({
        "status": "PENDING"
    })

@bp.get("/api/v1/contacts/friends/<account_id:str>/invites")
async def get_contact_invites(request, account_id):
    return json({
        "incoming": [],
        "outgoing": []
    })

@bp.post("/api/v1/contacts/friends/<account_id:str>/invites/<invite_id:str>/accept")
async def accept_contact_invite(request, account_id, invite_id):
    return json({
        "status": "ACCEPTED"
    })

@bp.post("/api/v1/contacts/friends/<account_id:str>/invites/<invite_id:str>/reject")
async def reject_contact_invite(request, account_id, invite_id):
    return empty(status=204)

@bp.delete("/api/v1/contacts/friends/<account_id:str>/friends/<friend_account_id:str>")
async def remove_contact_friend(request, account_id, friend_account_id):
    return empty(status=204)