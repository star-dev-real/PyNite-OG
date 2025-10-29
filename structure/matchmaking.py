from sanic import Blueprint, json
from sanic.response import empty
import json as json_module
from pathlib import Path
import configparser
from datetime import datetime
from .functions import MakeID

bp = Blueprint("matchmaking", url_prefix="/")


CONFIG_PATH = Path(__file__).parent.parent / "Config" / "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

@bp.get("/fortnite/api/matchmaking/session/findPlayer/<path:path>")
async def find_player(request, path):
    return empty(status=200)

@bp.get("/fortnite/api/game/v2/matchmakingservice/ticket/player/<path:path>")
async def get_matchmaking_ticket(request, path):
    bucket_id = request.args.get("bucketId", "")
    current_build_unique_id = bucket_id.split(":")[0] if ":" in bucket_id else ""
    
    response = json({
        "serviceUrl": "ws://127.0.0.1",
        "ticketType": "mms-player",
        "payload": "69=",
        "signature": "420="
    })
    
    
    response.cookies["currentbuildUniqueId"] = current_build_unique_id
    return response

@bp.get("/fortnite/api/game/v2/matchmaking/account/<account_id:str>/session/<session_id:str>")
async def get_matchmaking_session(request, account_id, session_id):
    return json({
        "accountId": account_id,
        "sessionId": session_id,
        "key": "AOJEv8uTFmUh7XM2328kq9rlAzeQ5xzWzPIiyKn2s7s="
    })

@bp.get("/fortnite/api/matchmaking/session/<session_id:str>")
async def get_session_details(request, session_id):
    
    game_server_ip = config.get("GameServer", "ip", fallback="127.0.0.1")
    game_server_port = config.getint("GameServer", "port", fallback=7777)
    
    
    current_build_unique_id = request.cookies.get("currentbuildUniqueId", "0")
    
    return json({
        "id": session_id,
        "ownerId": MakeID().replace("-", "").upper(),
        "ownerName": "[DS]fortnite-liveeugcec1c2e30ubrcore0a-z8hj-1968",
        "serverName": "[DS]fortnite-liveeugcec1c2e30ubrcore0a-z8hj-1968",
        "serverAddress": game_server_ip,
        "serverPort": game_server_port,
        "maxPublicPlayers": 220,
        "openPublicPlayers": 175,
        "maxPrivatePlayers": 0,
        "openPrivatePlayers": 0,
        "attributes": {
            "REGION_s": "EU",
            "GAMEMODE_s": "FORTATHENA",
            "ALLOWBROADCASTING_b": True,
            "SUBREGION_s": "GB",
            "DCID_s": "FORTNITE-LIVEEUGCEC1C2E30UBRCORE0A-14840880",
            "tenant_s": "Fortnite",
            "MATCHMAKINGPOOL_s": "Any",
            "STORMSHIELDDEFENSETYPE_i": 0,
            "HOTFIXVERSION_i": 0,
            "PLAYLISTNAME_s": "Playlist_DefaultSolo",
            "SESSIONKEY_s": MakeID().replace("-", "").upper(),
            "TENANT_s": "Fortnite",
            "BEACONPORT_i": 15009
        },
        "publicPlayers": [],
        "privatePlayers": [],
        "totalPlayers": 45,
        "allowJoinInProgress": False,
        "shouldAdvertise": False,
        "isDedicated": False,
        "usesStats": False,
        "allowInvites": False,
        "usesPresence": False,
        "allowJoinViaPresence": True,
        "allowJoinViaPresenceFriendsOnly": False,
        "buildUniqueId": current_build_unique_id,
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
        "started": False
    })

@bp.post("/fortnite/api/matchmaking/session/<path:path>/join")
async def join_session(request, path):
    return empty(status=204)

@bp.post("/fortnite/api/matchmaking/session/matchMakingRequest")
async def matchmaking_request(request):
    return json([])