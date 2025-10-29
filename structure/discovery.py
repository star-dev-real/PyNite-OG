from sanic import Blueprint, json
from sanic.response import empty
import json as json_module
from pathlib import Path

bp = Blueprint("discovery", url_prefix="/")

DISCOVERY_PATH = Path(__file__).parent.parent / "responses" / "Athena" / "Discovery" / "discovery_frontend.json"
try:
    with open(DISCOVERY_PATH, "r", encoding="utf-8") as f:
        DISCOVERY_DATA = json_module.load(f)
except Exception as e:
    print(f"Error loading discovery_frontend.json: {e}")
    DISCOVERY_DATA = {"v1": {}, "v2": {}}

@bp.post("*/api/v2/discovery/surface/<path:path>")
async def post_discovery_surface_v2(request, path):
    return json(DISCOVERY_DATA.get("v2", {}))

@bp.post("*/discovery/surface/<path:path>")
async def post_discovery_surface_v1(request, path):
    return json(DISCOVERY_DATA.get("v1", {}))

@bp.get("/fortnite/api/discovery/accessToken/<branch:str>")
async def get_discovery_access_token(request, branch):
    return json({
        "branchName": branch,
        "appId": "Fortnite",
        "token": "PyNitetokenlol"
    })

@bp.post("/links/api/fn/mnemonic")
async def post_mnemonic(request):
    mnemonic_array = []
    
    discovery_v2 = DISCOVERY_DATA.get("v2", {})
    if ("Panels" in discovery_v2 and 
        len(discovery_v2["Panels"]) > 1 and
        "Pages" in discovery_v2["Panels"][1] and
        len(discovery_v2["Panels"][1]["Pages"]) > 0 and
        "results" in discovery_v2["Panels"][1]["Pages"][0]):
        
        for result in discovery_v2["Panels"][1]["Pages"][0]["results"]:
            if "linkData" in result:
                mnemonic_array.append(result["linkData"])
    
    return json(mnemonic_array)

@bp.get("/links/api/fn/mnemonic/<playlist:str>/related")
async def get_mnemonic_related(request, playlist):
    response = {
        "parentLinks": [],
        "links": {}
    }
    
    if playlist:
        discovery_v2 = DISCOVERY_DATA.get("v2", {})
        if ("Panels" in discovery_v2 and 
            len(discovery_v2["Panels"]) > 1 and
            "Pages" in discovery_v2["Panels"][1] and
            len(discovery_v2["Panels"][1]["Pages"]) > 0 and
            "results" in discovery_v2["Panels"][1]["Pages"][0]):
            
            for result in discovery_v2["Panels"][1]["Pages"][0]["results"]:
                if ("linkData" in result and 
                    "mnemonic" in result["linkData"] and 
                    result["linkData"]["mnemonic"] == playlist):
                    response["links"][playlist] = result["linkData"]
    
    return json(response)

@bp.get("/links/api/fn/mnemonic/<path:path>")
async def get_mnemonic_wildcard(request, path):
    mnemonic = path.split("/")[-1] if "/" in path else path
    
    discovery_v2 = DISCOVERY_DATA.get("v2", {})
    if ("Panels" in discovery_v2 and 
        len(discovery_v2["Panels"]) > 1 and
        "Pages" in discovery_v2["Panels"][1] and
        len(discovery_v2["Panels"][1]["Pages"]) > 0 and
        "results" in discovery_v2["Panels"][1]["Pages"][0]):
        
        for result in discovery_v2["Panels"][1]["Pages"][0]["results"]:
            if ("linkData" in result and 
                "mnemonic" in result["linkData"] and 
                result["linkData"]["mnemonic"] == mnemonic):
                return json(result["linkData"])
    
    return json({}, status=404)

@bp.post("/api/v1/links/lock-status/<account_id:str>/check")
async def post_lock_status_check(request, account_id):
    response = {
        "results": [],
        "hasMore": False
    }
    
    body = request.json if request.json else {}
    link_codes = body.get("linkCodes", [])
    
    for link_code in link_codes:
        response["results"].append({
            "playerId": account_id,
            "linkCode": link_code,
            "lockStatus": "UNLOCKED",
            "lockStatusReason": "NONE",
            "isVisible": True
        })
    
    return json(response)