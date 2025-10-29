from sanic import Blueprint, json, Sanic
from sanic.response import empty
import os
from pathlib import Path
from functions import chooseTranslationsInJSON, getContentPages
import json as json_module

bp = Blueprint("contentpages", url_prefix="/content-pages")

SPARK_TRACKS_PATH = Path(__file__).parent.parent / "responses" / "Athena" / "sparkTracks.json"
SEASON_PASSES_PATH = Path(__file__).parent.parent / "responses" / "Athena" / "seasonPasses.json"
MOTD_PATH = Path(__file__).parent.parent / "responses" / "Athena" / "motd.json"

with open(SPARK_TRACKS_PATH, "r") as f:
    SPARK_TRACKS = json_module.load(f)

with open(SEASON_PASSES_PATH, "r") as f:
    SEASON_PASSES = json_module.load(f)

with open(MOTD_PATH, "r") as f:
    MOTD_DATA = json_module.load(f)


@bp.get("/content/api/pages/fortnite-game/spark-tracks")
async def get_spark_tracks(request):
    return json(SPARK_TRACKS)

@bp.get("/content/api/pages/fortnite-game/radio-stations")
async def get_radio_stations(request):
    return json({
        "_title": "Radio Stations",
        "radioStationList": {
            "_type": "RadioStationList",
            "stations": [
                {
                    "resourceID": "QWGQAynCdixzoLIdJl",
                    "stationImage": "https://fortnite-public-service-prod11.ol.epicgames.com/images/PyNitepfp.png",
                    "_type": "RadioStationItem",
                    "title": {
                        "ar": "الحفل الملكي",
                        "de": "Party Royale",
                        "en": "Party Royale",
                        "es": "Fiesta magistral",
                        "es-419": "Fiesta campal",
                        "fr": "Fête royale",
                        "it": "Party Reale",
                        "ja": "パーティーロイヤル",
                        "ko": "파티로얄",
                        "pl": "Królewska Impreza",
                        "pt-BR": "Festa Royale",
                        "ru": "Королевская вечеринка",
                        "tr": "Çılgın Parti",
                        "zh-CN": "空降派对",
                        "zh-Hant": "空降派對"
                    }
                }
            ]
        },
        "_noIndex": False,
        "_activeDate": "2024-06-13T10:00:00.000Z",
        "lastModified": "2024-06-12T20:12:56.271Z",
        "_locale": "en-US",
        "_templateName": "FortniteGameRadioStations",
        "_suggestedPrefetch": []
    })

@bp.get("/content/api/pages/fortnite-game/seasonpasses")
async def get_season_passes(request):
    season_passes = json_module.loads(json_module.dumps(SEASON_PASSES))  
    chooseTranslationsInJSON(season_passes, request)
    return json(season_passes)

@bp.get("/content/api/pages/<path:path>")
async def get_content_pages(request, path):
    content_pages = getContentPages(request)
    return json(content_pages)

@bp.post("/api/v1/fortnite-br/<path:path>/target")
async def post_fortnite_br_target(request, path):
    motd = json_module.loads(json_module.dumps(MOTD_DATA))  
    
    
    body = request.json if request.json else {}
    language = body.get("language")
    if not language and "parameters" in body:
        language = body["parameters"].get("language")
    
    chooseTranslationsInJSON(motd, request, language)
    
    
    if "tags" in body:
        tags = body["tags"]
        for item in motd.get("contentItems", []):
            item["placements"] = []
            for tag in tags:
                item["placements"].append({
                    "trackingId": "PyNitestrackingidlol",
                    "tag": tag,
                    "position": 0
                })
    
    return json(motd)