from sanic import Blueprint, json
from sanic.response import empty, raw
import json as json_module
from pathlib import Path
import configparser
import random
from datetime import datetime
from .functions import MakeID, GetVersionInfo, getTheater

bp = Blueprint("main", url_prefix="/")

CONFIG_PATH = Path(__file__).parent.parent / "Config" / "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

TOURNAMENT_AND_HISTORY = {}
TOURNAMENT = {}
HISTORY = []
LEADERBOARD = {"entries": [], "entryTemplate": {}}
HERO_NAMES = ["Player1", "Player2", "Player3"]
EPIC_SETTINGS = {}
DISCOVERY_API_ASSETS = {}
ATHENA_PROFILE = {"items": {}, "rvn": 1, "commandRevision": 1}
CATALOG_CONFIG = {}

@bp.get("/clearitemsforshop")
async def clear_items_for_shop(request):
    return raw("Failed, there are no items to remove", content_type="text/plain")

@bp.get("/eulatracking/api/shared/agreements/fn<path:path>")
async def eula_tracking(request, path):
    return json({})

@bp.get("/fortnite/api/game/v2/friendcodes/<path:path>/epic")
async def get_friend_codes(request, path):
    return json([
        {
            "codeId": "PYNITES3RV3R",
            "codeType": "CodeToken:FounderFriendInvite",
            "dateCreated": "2024-04-02T21:37:00.420Z"
        },
        {
            "codeId": "playeereq",
            "codeType": "CodeToken:FounderFriendInvite_XBOX",
            "dateCreated": "2024-04-02T21:37:00.420Z"
        },
        {
            "codeId": "pynitecodelol",
            "codeType": "CodeToken:MobileInvite",
            "dateCreated": "2024-04-02T21:37:00.420Z"
        }
    ])

@bp.get("/launcher/api/public/distributionpoints/")
async def get_distribution_points(request):
    return json({
        "distributions": [
            "https://epicgames-download1.akamaized.net/",
            "https://download.epicgames.com/",
            "https://download2.epicgames.com/",
            "https://download3.epicgames.com/",
            "https://download4.epicgames.com/",
            "https://pynite.ol.epicgames.com/"
        ]
    })

@bp.get("/launcher/api/public/assets/<path:path>")
async def get_launcher_assets(request, path):
    return json({
        "appName": "FortniteContentBuilds",
        "labelName": "PyNiteOG",
        "buildVersion": "++Fortnite+Release-20.00-CL-19458861-Windows",
        "catalogItemId": "5cb97847cee34581afdbc445400e2f77",
        "expires": "9999-12-31T23:59:59.999Z",
        "items": {
            "MANIFEST": {
                "signature": "PyNiteOG",
                "distribution": "https://pynite.ol.epicgames.com/",
                "path": "Builds/Fortnite/Content/CloudDir/PyNiteOG.manifest",
                "hash": "55bb954f5596cadbe03693e1c06ca73368d427f3",
                "additionalDistributions": []
            },
            "CHUNKS": {
                "signature": "PyNiteOG",
                "distribution": "https://pynite.ol.epicgames.com/",
                "path": "Builds/Fortnite/Content/CloudDir/PyNiteOG.manifest",
                "additionalDistributions": []
            }
        },
        "assetId": "FortniteContentBuilds"
    })

@bp.get("/Builds/Fortnite/Content/CloudDir/<path:path>")
async def get_build_files(request, path):
    # Return empty for now - you can add file serving later
    return empty(status=404)

@bp.post("/fortnite/api/game/v2/grant_access/<path:path>")
async def grant_access(request, path):
    return json({})

@bp.post("/api/v1/user/setting")
async def post_user_setting(request):
    return json([])

@bp.get("/waitingroom/api/waitingroom")
async def get_waiting_room(request):
    return empty(status=204)

@bp.get("/socialban/api/public/v1/<path:path>")
async def get_social_ban(request, path):
    return json({
        "bans": [],
        "warnings": []
    })

@bp.get("/fortnite/api/game/v2/events/tournamentandhistory/<path:path>")
async def get_tournament_and_history(request, path):
    return json(TOURNAMENT_AND_HISTORY)

@bp.get("/fortnite/api/statsv2/account/<account_id:str>")
async def get_stats_v2(request, account_id):
    return json({
        "startTime": 0,
        "endTime": 0,
        "stats": {},
        "accountId": account_id
    })

@bp.get("/statsproxy/api/statsv2/account/<account_id:str>")
async def get_stats_proxy(request, account_id):
    return json({
        "startTime": 0,
        "endTime": 0,
        "stats": {},
        "accountId": account_id
    })

@bp.get("/fortnite/api/stats/accountId/<account_id:str>/bulk/window/alltime")
async def get_stats_bulk(request, account_id):
    return json({
        "startTime": 0,
        "endTime": 0,
        "stats": {},
        "accountId": account_id
    })

@bp.get("/d98eeaac-2bfa-4bf4-8a59-bdc95469c693")
async def get_media_presentation(request):
    return json({
        "playlist": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPE1QRCB4bWxucz0idXJuOm1wZWc6ZGFzaDpzY2hlbWE6bXBkOjIwMTEiIHhtbG5zOnhzaT0iaHR0cDovL3d3dy53My5vcmcvMjAwMS9YTUxTY2hlbWEtaW5zdGFuY2UiIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB4c2k6c2NoZW1hTG9jYXRpb249InVybjptcGVnOkRBU0g6c2NoZW1hOk1QRDoyMDExIGh0dHA6Ly9zdGFuZGFyZHMuaXNvLm9yZy9pdHRmL1B1YmxpY2x5QXZhaWxhYmxlU3RhbmRhcmRzL01QRUctREFTSF9zY2hlbWFfZmlsZXMvREFTSC1NUEQueHNkIiBwcm9maWxlcz0idXJuOm1wZWc6ZGFzaDpwcm9maWxlOmlzb2ZmLWxpdmU6MjAxMSIgdHlwZT0ic3RhdGljIiBtZWRpYVByZXNlbnRhdGlvbkR1cmF0aW9uPSJQVDMwLjIxM1MiIG1heFNlZ21lbnREdXJhdGlvbj0iUFQyLjAwMFMiIG1pbkJ1ZmZlclRpbWU9IlBUNC4xMDZTIj4KICA8QmFzZVVSTD5odHRwczovL3BpbGdyaW0ucXN0di5vbi5lcGljZ2FtZXMuY29tL3VtbXFVcUNTRlVXZVFmelR2cy9mMjUyOGZhMS01ZjMwLTQyZmYtOGFlNS1hMDNlM2IwMjNhMGEvPC9CYXNlVVJMPgogIDxQcm9ncmFtSW5mb3JtYXRpb24+PC9Qcm9ncmFtSW5mb3JtYXRpb24+CiAgPFBlcmlvZCBpZD0iMCIgc3RhcnQ9IlBUMFMiPgogICAgPEFkYXB0YXRpb25TZXQgaWQ9IjAiIGNvbnRlbnRUeXBlPSJhdWRpbyIgc3RhcnRXaXRoU0FQPSIxIiBzZWdtZW50QWxpZ25tZW50PSJ0cnVlIiBiaXRzdHJlYW1Td2l0Y2hpbmc9InRydWUiPgogICAgICA8UmVwcmVzZW50YXRpb24gaWQ9IjAiIGF1ZGlvU2FtcGxpbmdSYXRlPSI0ODAwMCIgYmFuZHdpZHRoPSIxMjgwMDAiIG1pbWVUeXBlPSJhdWRpby9tcDQiIGNvZGVjcz0ibXA0YS40MC4yIj4KICAgICAgICA8U2VnbWVudFRlbXBsYXRlIGR1cmF0aW9uPSIyMDAwMDAwIiB0aW1lc2NhbGU9IjEwMDAwMDAiIGluaXRpYWxpemF0aW9uPSJpbml0XyRSZXByZXNlbnRhdGlvbklEJC5tcDQiIG1lZGlhPSJzZWdtZW50XyRSZXByZXNlbnRhdGlvbklEJF8kTnVtYmVyJC5tNHMiIHN0YXJ0TnVtYmVyPSIxIj48L1NlZ21lbnRUZW1wbGF0ZT4KICAgICAgICA8QXVkaW9DaGFubmVsQ29uZmlndXJhdGlvbiBzY2hlbWVJZFVyaT0idXJuOm1wZWc6ZGFzaDoyMzAwMzozOmF1ZGlvX2NoYW5uZWxfY29uZmlndXJhdGlvbjoyMDExIiB2YWx1ZT0iMiI+PC9BdWRpb0NoYW5uZWxDb25maWd1cmF0aW9uPgogICAgICA8L1JlcHJlc2VudGF0aW9uPgogICAgPC9BZGFwdGF0aW9uU2V0PgogIDwvUGVyaW9kPgo8L01QRD4=",
        "playlistType": "application/dash+xml",
        "metadata": {
            "assetId": "",
            "baseUrls": [
                "https://fortnite-public-service-prod11.ol.epicgames.com/ummqUqCSFUWeQfzTvs/f2528fa1-5f30-42ff-8ae5-a03e3b023a0a/"
            ],
            "supportsCaching": True,
            "ucp": "a",
            "version": "f2528fa1-5f30-42ff-8ae5-a03e3b023a0a"
        }
    })

@bp.post("/fortnite/api/feedback/<path:path>")
async def post_feedback(request, path):
    return empty(status=200)

@bp.post("/fortnite/api/statsv2/query")
async def post_stats_query(request):
    return json([])

@bp.post("/statsproxy/api/statsv2/query")
async def post_stats_proxy_query(request):
    return json([])

@bp.post("/fortnite/api/game/v2/events/v2/setSubgroup/<path:path>")
async def set_subgroup(request, path):
    return empty(status=204)

@bp.get("/fortnite/api/game/v2/enabled_features")
async def get_enabled_features(request):
    return json([])

@bp.get("/api/v1/events/Fortnite/download/<path:path>")
async def get_events_download(request, path):
    return json(TOURNAMENT)

@bp.get("/api/v1/events/Fortnite/<event_id:str>/history/<account_id:str>")
async def get_event_history(request, event_id, account_id):
    history = json_module.loads(json_module.dumps(HISTORY)) if HISTORY else [{
        "scoreKey": {"eventId": event_id},
        "teamId": account_id,
        "teamAccountIds": [account_id]
    }]
    return json(history)

@bp.get("/api/v1/leaderboards/Fortnite/<event_id:str>/<event_window_id:str>/<account_id:str>")
async def get_leaderboards(request, event_id, event_window_id, account_id):
    leaderboard_data = {
        "eventId": event_id,
        "eventWindowId": event_window_id,
        "entries": []
    }
    
    # Add some dummy entries
    for i in range(10):
        leaderboard_data["entries"].append({
            "eventId": event_id,
            "eventWindowId": event_window_id,
            "teamAccountIds": [f"Player{i}"],
            "teamId": f"Player{i}",
            "pointsEarned": 100 - i,
            "score": 100 - i,
            "rank": i + 1
        })
    
    return json(leaderboard_data)

@bp.get("/fortnite/api/game/v2/twitch/<path:path>")
async def get_twitch(request, path):
    return empty(status=200)

@bp.get("/fortnite/api/game/v2/world/info")
async def get_world_info(request):
    worldstw = getTheater(request)
    return json(worldstw)

@bp.post("/fortnite/api/game/v2/chat/<path:path>/pc")
async def post_chat(request, path):
    return json({"GlobalChatRooms": [{"roomName": "pyniteglobal"}]})

@bp.post("/fortnite/api/game/v2/chat/<path:path>/recommendGeneralChatRooms/pc")
async def post_chat_recommend(request, path):
    return json({})

@bp.get("/presence/api/v1/_/<path:path>/last-online")
async def get_last_online(request, path):
    return json({})

@bp.get("/fortnite/api/receipts/v1/account/<path:path>/receipts")
async def get_receipts(request, path):
    return json([])

@bp.get("/fortnite/api/game/v2/leaderboards/cohort/<account_id:str>")
async def get_cohort_leaderboards(request, account_id):
    playlist = request.args.get("playlist", "")
    return json({
        "accountId": account_id,
        "cohortAccounts": [
            account_id,
            "PyNite",
            "TI93",
            "PRO100KatYT",
            "Playeereq",
            "Matteoki"
        ],
        "expiresAt": "9999-12-31T00:00:00.000Z",
        "playlist": playlist
    })

@bp.post("/fortnite/api/leaderboards/type/group/stat/<stat_name:str>/window/<stat_window:str>")
async def post_group_leaderboards(request, stat_name, stat_window):
    body = request.json if request.json else []
    entries = []
    
    for account_id in body:
        entries.append({
            "accountId": account_id,
            "value": random.randint(1, 68)
        })
    
    return json({
        "entries": entries,
        "statName": stat_name,
        "statWindow": stat_window
    })

@bp.post("/fortnite/api/leaderboards/type/global/stat/<stat_name:str>/window/<stat_window:str>")
async def post_global_leaderboards(request, stat_name, stat_window):
    entries = []
    
    for hero_name in HERO_NAMES:
        entries.append({
            "accountId": hero_name,
            "value": random.randint(1, 68)
        })
    
    return json({
        "entries": entries,
        "statName": stat_name,
        "statWindow": stat_window
    })

@bp.get("/fortnite/api/game/v2/homebase/allowed-name-chars")
async def get_allowed_name_chars(request):
    return json({
        "ranges": [
            48, 57, 65, 90, 97, 122, 192, 255, 260, 265, 280, 281, 286, 287, 304, 305,
            321, 324, 346, 347, 350, 351, 377, 380, 1024, 1279, 1536, 1791, 4352, 4607,
            11904, 12031, 12288, 12351, 12352, 12543, 12592, 12687, 12800, 13055, 13056,
            13311, 13312, 19903, 19968, 40959, 43360, 43391, 44032, 55215, 55216, 55295,
            63744, 64255, 65072, 65103, 65281, 65470, 131072, 173791, 194560, 195103
        ],
        "singlePoints": [32, 39, 45, 46, 95, 126],
        "excludedPoints": [208, 215, 222, 247]
    })

@bp.post("/datarouter/api/v1/public/data")
async def post_datarouter(request):
    return empty(status=204)

@bp.post("/api/v1/assets/Fortnite/<path:path>")
async def post_assets(request, path):
    body = request.json if request.json else {}
    
    if "FortCreativeDiscoverySurface" in body and body["FortCreativeDiscoverySurface"] == 0:
        return json(DISCOVERY_API_ASSETS)
    else:
        return json({
            "FortCreativeDiscoverySurface": {
                "meta": {
                    "promotion": body.get("FortCreativeDiscoverySurface", 0)
                },
                "assets": {}
            }
        })

@bp.get("/region")
async def get_region(request):
    return json({
        "continent": {
            "code": "EU",
            "geoname_id": 6255148,
            "names": {
                "de": "Europa",
                "en": "Europe",
                "es": "Europa",
                "fr": "Europe",
                "ja": "ヨーロッパ",
                "pt-BR": "Europa",
                "ru": "Европа",
                "zh-CN": "欧洲"
            }
        },
        "country": {
            "geoname_id": 2635167,
            "is_in_european_union": False,
            "iso_code": "GB",
            "names": {
                "de": "UK",
                "en": "United Kingdom",
                "es": "RU",
                "fr": "Royaume Uni",
                "ja": "英国",
                "pt-BR": "Reino Unido",
                "ru": "Британия",
                "zh-CN": "英国"
            }
        },
        "subdivisions": [
            {
                "geoname_id": 6269131,
                "iso_code": "ENG",
                "names": {
                    "de": "England",
                    "en": "England",
                    "es": "Inglaterra",
                    "fr": "Angleterre",
                    "ja": "イングランド",
                    "pt-BR": "Inglaterra",
                    "ru": "Англия",
                    "zh-CN": "英格兰"
                }
            },
            {
                "geoname_id": 3333157,
                "iso_code": "KEC",
                "names": {
                    "en": "Royal Kensington and Chelsea"
                }
            }
        ]
    })

@bp.route("/v1/epic-settings/public/users/<path:path>/values", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def epic_settings(request, path):
    return json(EPIC_SETTINGS)

@bp.get("/fortnite/api/game/v2/br-inventory/account/<path:path>")
async def get_br_inventory(request, path):
    return json({
        "stash": {
            "globalcash": 5000
        }
    })