from sanic import Blueprint, json
import json as json_module
from pathlib import Path

bp = Blueprint("privacy", url_prefix="/")


PRIVACY_PATH = Path(__file__).parent.parent / "responses" / "privacy.json"
with open(PRIVACY_PATH, "r") as f:
    PRIVACY_DATA = json_module.load(f)

@bp.get("/fortnite/api/game/v2/privacy/account/<account_id:str>")
async def get_privacy_settings(request, account_id):
    privacy_data = json_module.loads(json_module.dumps(PRIVACY_DATA))  
    privacy_data["accountId"] = account_id
    
    return json(privacy_data)

@bp.post("/fortnite/api/game/v2/privacy/account/<account_id:str>")
async def update_privacy_settings(request, account_id):
    body = request.json if request.json else {}
    
    
    PRIVACY_DATA["accountId"] = account_id
    if "optOutOfPublicLeaderboards" in body:
        PRIVACY_DATA["optOutOfPublicLeaderboards"] = body["optOutOfPublicLeaderboards"]
    
    
    with open(PRIVACY_PATH, "w") as f:
        json_module.dump(PRIVACY_DATA, f, indent=2)
    
    return json(PRIVACY_DATA)