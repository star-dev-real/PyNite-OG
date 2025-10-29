import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import base64
from typing import Dict, Any, List, Union


from xmpp import xmpp_server


with open(Path(__file__).parent.parent / "responses" / "catalog.json", "r") as f:
    CATALOG_DATA = json.load(f)

with open(Path(__file__).parent.parent / "Config" / "catalog_config.json", "r") as f:
    CATALOG_CONFIG = json.load(f)

with open(Path(__file__).parent.parent / "responses" / "Campaign" / "worldstw.json", "r") as f:
    THEATER_DATA = json.load(f)

with open(Path(__file__).parent.parent / "responses" / "contentpages.json", "r") as f:
    CONTENT_PAGES_DATA = json.load(f)

with open(Path(__file__).parent.parent / "responses" / "Campaign" / "survivorData.json", "r") as f:
    SURVIVOR_DATA = json.load(f)

async def sleep(ms):
    await asyncio.sleep(ms / 1000)

def GetVersionInfo(req):
    memory = {
        "season": 0,
        "build": 0.0,
        "CL": "",
        "lobby": ""
    }

    user_agent = req.headers.get("user-agent", "")
    if not user_agent:
        return memory

    CL = ""
    
    try:
        
        parts = user_agent.split("-")
        if len(parts) > 3:
            build_id_part = parts[3].split(",")[0]
            if build_id_part.isdigit():
                CL = build_id_part
            else:
                build_id_part = parts[3].split(" ")[0]
                if build_id_part.isdigit():
                    CL = build_id_part
    except Exception:
        try:
            
            parts = user_agent.split("-")
            if len(parts) > 1:
                build_id_part = parts[1].split("+")[0]
                if build_id_part.isdigit():
                    CL = build_id_part
        except Exception:
            pass

    try:
        
        if "Release-" in user_agent:
            build_part = user_agent.split("Release-")[1].split("-")[0]
            
            
            if build_part.count(".") == 2:
                parts = build_part.split(".")
                build_part = f"{parts[0]}.{parts[1]}{parts[2]}"
            
            
            season_num = int(build_part.split(".")[0])
            build_num = float(build_part)
            
            memory["season"] = season_num
            memory["build"] = build_num
            memory["CL"] = CL
            memory["lobby"] = f"LobbySeason{season_num}"
            
        else:
            raise ValueError("No Release- found in user-agent")
            
    except Exception:
        
        memory["season"] = 2
        memory["build"] = 2.0
        memory["CL"] = CL
        memory["lobby"] = "LobbyWinterDecor"

    return memory

def getItemShop():
    catalog = json.loads(json.dumps(CATALOG_DATA))
    
    try:
        for key, value in CATALOG_CONFIG.items():
            if isinstance(value.get("itemGrants"), list) and value["itemGrants"]:
                catalog_entry = {
                    "devName": "", "offerId": "", "fulfillmentIds": [], "dailyLimit": -1, 
                    "weeklyLimit": -1, "monthlyLimit": -1, "categories": [], 
                    "prices": [{"currencyType": "MtxCurrency", "currencySubType": "", 
                               "regularPrice": 0, "finalPrice": 0, 
                               "saleExpiration": "9999-12-02T01:12:00Z", "basePrice": 0}],
                    "meta": {"NewDisplayAssetPath": "", "SectionId": "Featured", 
                            "LayoutId": "PyNiteOG.99", "TileSize": "Small", 
                            "AnalyticOfferGroupId": "PyNiteOG/Attitude8", 
                            "FirstSeen": "2/2/2020"},
                    "matchFilter": "", "filterWeight": 0, "appStoreId": [], 
                    "requirements": [], "offerType": "StaticPrice", 
                    "giftInfo": {"bIsEnabled": False, "forcedGiftBoxTemplateId": "", 
                                "purchaseRequirements": [], "giftRecordIds": []},
                    "refundable": True,
                    "metaInfo": [
                        {"key": "NewDisplayAssetPath", "value": "="},
                        {"key": "SectionId", "value": "Featured"},
                        {"key": "LayoutId", "value": "PyNiteOG.99"},
                        {"key": "TileSize", "value": "Small"},
                        {"key": "AnalyticOfferGroupId", "value": "PyNiteOG/Attitude8"},
                        {"key": "FirstSeen", "value": "2/2/2020"}
                    ],
                    "displayAssetPath": "", "itemGrants": [], "sortPriority": 0, 
                    "catalogGroupPriority": 0
                }

                if key.lower().startswith("daily"):
                    for storefront in catalog["storefronts"]:
                        if storefront["name"] == "BRDailyStorefront":
                            catalog_entry["requirements"] = []
                            catalog_entry["itemGrants"] = []

                            for item_grant in value["itemGrants"]:
                                if isinstance(item_grant, str) and item_grant:
                                    catalog_entry["devName"] = value["itemGrants"][0]
                                    catalog_entry["offerId"] = value["itemGrants"][0]
                                    
                                    catalog_entry["requirements"].append({
                                        "requirementType": "DenyOnItemOwnership",
                                        "requiredId": item_grant,
                                        "minQuantity": 1
                                    })
                                    catalog_entry["itemGrants"].append({
                                        "templateId": item_grant,
                                        "quantity": 1
                                    })

                            catalog_entry["prices"][0]["basePrice"] = value["price"]
                            catalog_entry["prices"][0]["regularPrice"] = value["price"]
                            catalog_entry["prices"][0]["finalPrice"] = value["price"]
                            
                            
                            catalog_entry["sortPriority"] = -1

                            if catalog_entry["itemGrants"]:
                                storefront["catalogEntries"].append(catalog_entry)

                elif key.lower().startswith("featured"):
                    for storefront in catalog["storefronts"]:
                        if storefront["name"] == "BRWeeklyStorefront":
                            catalog_entry["requirements"] = []
                            catalog_entry["itemGrants"] = []

                            for item_grant in value["itemGrants"]:
                                if isinstance(item_grant, str) and item_grant:
                                    catalog_entry["devName"] = value["itemGrants"][0]
                                    catalog_entry["offerId"] = value["itemGrants"][0]
                                    
                                    catalog_entry["requirements"].append({
                                        "requirementType": "DenyOnItemOwnership",
                                        "requiredId": item_grant,
                                        "minQuantity": 1
                                    })
                                    catalog_entry["itemGrants"].append({
                                        "templateId": item_grant,
                                        "quantity": 1
                                    })

                            catalog_entry["prices"][0]["basePrice"] = value["price"]
                            catalog_entry["prices"][0]["regularPrice"] = value["price"]
                            catalog_entry["prices"][0]["finalPrice"] = value["price"]
                            
                            catalog_entry["meta"]["TileSize"] = "Normal"
                            catalog_entry["metaInfo"][3]["value"] = "Normal"

                            if catalog_entry["itemGrants"]:
                                storefront["catalogEntries"].append(catalog_entry)
    except Exception as e:
        print(f"Error in getItemShop: {e}")

    return catalog

def getTheater(req):
    memory = GetVersionInfo(req)
    theater = json.dumps(THEATER_DATA)
    season_key = f"Season{memory['season']}"

    try:
        
        if memory["build"] >= 30.20:
            theater = theater.replace("/Game/World/ZoneThemes", "/STW_Zones/World/ZoneThemes")
            theater = theater.replace('"DataTable\'/Game/', '"/Script/Engine.DataTable\'/Game/')

        if memory["build"] >= 15.30:
            theater = theater.replace("/Game/", "/SaveTheWorld/")
            theater = theater.replace('"DataTable\'/SaveTheWorld/', '"DataTable\'/Game/')

        
        now = datetime.now()
        
        if memory["season"] >= 9:
            
            refresh_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            
            if now.hour < 6:
                refresh_time = now.replace(hour=5, minute=59, second=59, microsecond=999999)
            elif now.hour < 12:
                refresh_time = now.replace(hour=11, minute=59, second=59, microsecond=999999)
            elif now.hour < 18:
                refresh_time = now.replace(hour=17, minute=59, second=59, microsecond=999999)
            else:
                refresh_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        refresh_iso = refresh_time.isoformat() + 'Z'
        theater = theater.replace("2017-07-25T23:59:59.999Z", refresh_iso)
        
    except Exception as e:
        print(f"Error in getTheater: {e}")

    theater = json.loads(theater)

    
    if "Seasonal" in theater:
        if season_key in theater["Seasonal"]:
            seasonal_data = theater["Seasonal"][season_key]
            theater["theaters"].extend(seasonal_data.get("theaters", []))
            theater["missions"].extend(seasonal_data.get("missions", []))
            theater["missionAlerts"].extend(seasonal_data.get("missionAlerts", []))
        del theater["Seasonal"]

    return theater

def chooseTranslationsInJSON(obj, req, target_language=""):
    if not target_language:
        accept_language = req.headers.get("accept-language", "en")
        if "-" in accept_language and accept_language not in ["es-419", "pt-BR"]:
            target_language = accept_language.split("-")[0]
        else:
            target_language = accept_language

    def process_item(item):
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, dict):
                    if target_language in value or "en" in value:
                        item[key] = value.get(target_language, value.get("en"))
                    else:
                        process_item(value)
                elif isinstance(value, list):
                    for list_item in value:
                        process_item(list_item)
        elif isinstance(item, list):
            for list_item in item:
                process_item(list_item)

    process_item(obj)

def getContentPages(req):
    memory = GetVersionInfo(req)
    contentpages = json.loads(json.dumps(CONTENT_PAGES_DATA))

    chooseTranslationsInJSON(contentpages, req)

    news_modes = ["savetheworldnews", "battleroyalenews"]
    
    try:
        if memory["build"] < 5.30:
            for mode in news_modes:
                if mode in contentpages:
                    contentpages[mode]["news"]["messages"][0]["image"] = "https://fortnite-public-service-prod11.ol.epicgames.com/images/discord-s.png"
                    contentpages[mode]["news"]["messages"][1]["image"] = "https://fortnite-public-service-prod11.ol.epicgames.com/images/PyNite-s.png"
    except Exception as e:
        print(f"Error updating news images: {e}")

    try:
        if "dynamicbackgrounds" in contentpages:
            backgrounds = contentpages["dynamicbackgrounds"]["backgrounds"]["backgrounds"]
            season_bg = f"season{memory['season']}{'00' if memory['season'] >= 21 else ''}"
            
            if backgrounds:
                backgrounds[0]["stage"] = season_bg
                if len(backgrounds) > 1:
                    backgrounds[1]["stage"] = season_bg

        
        season = memory["season"]
        build = memory["build"]
        
        background_configs = {
            9: {"lobby": {"backgroundimage": "", "stage": "default"}},
            10: {"backgrounds": [{"stage": "seasonx"}, {"stage": "seasonx"}]},
            20: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-bp20-lobby-2048x1024-d89eb522746c.png"}]},
            21: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/s21-lobby-background-2048x1024-2e7112b25dc3.jpg"}]},
            22: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-bp22-lobby-square-2048x2048-2048x2048-e4e90c6e8018.jpg"}]},
            23: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-bp23-lobby-2048x1024-2048x1024-26f2c1b27f63.png"}]},
            24: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-ch4s2-bp-lobby-4096x2048-edde08d15f7e.jpg"}]},
            25: {"backgrounds": [
                {"backgroundimage": "https://cdn2.unrealengine.com/s25-lobby-4k-4096x2048-4a832928e11f.jpg"},
                {"backgroundimage": "https://cdn2.unrealengine.com/fn-shop-ch4s3-04-1920x1080-785ce1d90213.png"}
            ]},
            27: {"backgrounds": [{"stage": "rufus"}]}
        }

        
        if season in background_configs:
            config = background_configs[season]
            if "lobby" in config and "lobby" in contentpages:
                contentpages["lobby"].update(config["lobby"])
            if "backgrounds" in config and backgrounds:
                for i, bg_config in enumerate(config["backgrounds"]):
                    if i < len(backgrounds):
                        backgrounds[i].update(bg_config)

        
        build_configs = {
            9.30: {"lobby": {"stage": "summer"}},
            11.10: {"backgrounds": [{"stage": "fortnitemares"}, {"stage": "fortnitemares"}]},
            11.31: {"backgrounds": [{"stage": "winter19"}, {"stage": "winter19"}]},
            11.40: {"backgrounds": [{"stage": "winter19"}, {"stage": "winter19"}]},
            19.01: {
                "backgrounds": [{
                    "stage": "winter2021",
                    "backgroundimage": "https://cdn2.unrealengine.com/t-bp19-lobby-xmas-2048x1024-f85d2684b4af.png"
                }],
                "subgameinfo": {"battleroyale": {"image": "https://cdn2.unrealengine.com/19br-wf-subgame-select-512x1024-16d8bb0f218f.jpg"}},
                "specialoffervideo": {"bSpecialOfferEnabled": "true"}
            },
            20.40: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-bp20-40-armadillo-glowup-lobby-2048x2048-2048x2048-3b83b887cc7f.jpg"}]},
            21.10: {"backgrounds": [{"stage": "season2100"}]},
            21.30: {"backgrounds": [{
                "backgroundimage": "https://cdn2.unrealengine.com/nss-lobbybackground-2048x1024-f74a14565061.jpg",
                "stage": "season2130"
            }]},
            23.10: {
                "backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-bp23-winterfest-lobby-square-2048x2048-2048x2048-277a476e5ca6.png"}],
                "specialoffervideo": {"bSpecialOfferEnabled": "true"}
            },
            25.11: {"backgrounds": [{"backgroundimage": "https://cdn2.unrealengine.com/t-s25-14dos-lobby-4096x2048-2be24969eee3.jpg"}]}
        }

        if build in build_configs:
            config = build_configs[build]
            for key, value in config.items():
                if key in contentpages:
                    if isinstance(value, dict):
                        contentpages[key].update(value)
                    elif key == "backgrounds" and backgrounds:
                        for i, bg_config in enumerate(value):
                            if i < len(backgrounds):
                                backgrounds[i].update(bg_config)

        
        if not any(bg.get("backgroundimage") for bg in backgrounds if bg.get("backgroundimage")):
            backgrounds[0].update({
                "stage": "defaultnotris",
                "backgroundimage": "https://fortnite-public-service-prod11.ol.epicgames.com/images/lightlobbybg.png"
            })

    except Exception as e:
        print(f"Error configuring content pages: {e}")

    return contentpages

def MakeSurvivorAttributes(templateId):
    survivor_attributes = {
        "level": 1,
        "item_seen": False,
        "squad_slot_idx": -1,
        "building_slot_used": -1
    }

    
    fixed_attrs = SURVIVOR_DATA.get("fixedAttributes", {})
    if templateId in fixed_attrs:
        survivor_attributes.update(fixed_attrs[templateId])

    
    if "gender" not in survivor_attributes:
        survivor_attributes["gender"] = str(random.randint(1, 2))  

    
    if "managerSynergy" not in survivor_attributes:
        bonuses = SURVIVOR_DATA.get("bonuses", [])
        if bonuses:
            survivor_attributes["set_bonus"] = random.choice(bonuses)

    
    if "personality" not in survivor_attributes:
        personalities = SURVIVOR_DATA.get("personalities", [])
        if personalities:
            survivor_attributes["personality"] = random.choice(personalities)

    
    if "portrait" not in survivor_attributes:
        portrait_factor = survivor_attributes.get("managerSynergy", survivor_attributes.get("personality", ""))
        gender = survivor_attributes["gender"]
        
        portraits = SURVIVOR_DATA.get("portraits", {})
        if portrait_factor in portraits and gender in portraits[portrait_factor]:
            available_portraits = portraits[portrait_factor][gender]
            if available_portraits:
                survivor_attributes["portrait"] = random.choice(available_portraits)

    return survivor_attributes

def MakeID():
    return str(uuid.uuid4())

async def sendXmppMessageToAll(body):
    """Send XMPP message to all connected clients"""
    if isinstance(body, dict):
        body = json.dumps(body)
    
    
    if xmpp_server and hasattr(xmpp_server, 'clients'):
        for client in xmpp_server.clients:
            try:
                
                import xml.etree.ElementTree as ET
                message = ET.Element("message", {
                    "from": "xmpp-admin@prod.ol.epicgames.com",
                    "xmlns": "jabber:client",
                    "to": client['jid']
                })
                body_elem = ET.SubElement(message, "body")
                body_elem.text = body
                
                
                message_str = ET.tostring(message, encoding='unicode', short_empty_elements=False)
                await client['ws'].send(message_str)
            except Exception as e:
                print(f"Error sending XMPP message to {client['jid']}: {e}")

def DecodeBase64(string):
    return base64.b64decode(string).decode('utf-8')


__all__ = [
    'sleep',
    'GetVersionInfo', 
    'getItemShop',
    'getTheater',
    'chooseTranslationsInJSON',
    'getContentPages',
    'MakeSurvivorAttributes',
    'MakeID',
    'sendXmppMessageToAll',
    'DecodeBase64'
]