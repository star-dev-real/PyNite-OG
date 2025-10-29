from sanic import Blueprint, json
from sanic.response import empty
from datetime import datetime
from .functions import MakeID

bp = Blueprint("party", url_prefix="/")

@bp.get("/party/api/v1/Fortnite/user/<path:path>")
async def get_fortnite_user_parties(request, path):
    return json({
        "current": [],
        "pending": [],
        "invites": [],
        "pings": []
    })

@bp.post("/party/api/v1/Fortnite/parties")
async def create_party(request):
    body = request.json if request.json else {}
    
    if not body.get("join_info") or not body["join_info"].get("connection"):
        return json({})
    
    join_info = body["join_info"]
    connection = join_info["connection"]
    
    account_id = ""
    if connection.get("id"):
        account_id = connection["id"].split("@prod")[0]
    
    current_time = datetime.utcnow().isoformat() + "Z"
    
    return json({
        "id": MakeID().replace("-", ""),
        "created_at": current_time,
        "updated_at": current_time,
        "config": {
            "type": "DEFAULT",
            "discoverability": "ALL",
            "sub_type": "default",
            "invite_ttl": 14400,
            "intention_ttl": 60,
            **body.get("config", {})  
        },
        "members": [{
            "account_id": account_id,
            "meta": join_info.get("meta", {}),
            "connections": [
                {
                    "id": connection.get("id", ""),
                    "connected_at": current_time,
                    "updated_at": current_time,
                    "yield_leadership": False,
                    "meta": connection.get("meta", {})
                }
            ],
            "revision": 0,
            "updated_at": current_time,
            "joined_at": current_time,
            "role": "CAPTAIN"
        }],
        "applicants": [],
        "meta": body.get("meta", {}),
        "invites": [],
        "revision": 0,
        "intentions": []
    })

@bp.route("/party/api/v1/Fortnite/parties/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def handle_party_operations(request, path):
    return empty(status=204)