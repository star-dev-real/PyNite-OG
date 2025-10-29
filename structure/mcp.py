import os
import json
import configparser
from datetime import datetime
from sanic import Blueprint, response
from . import functions  
import random

bp = Blueprint("mcp", url_prefix="/")

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "..", "Config", "config.ini"))

catalog = functions.getItemShop()

@bp.middleware("request")
async def handle_profiles_and_check_profileid(request):
    if request.path.lower().startswith("/fortnite/api/game/v2/profile/") and "profileId" not in request.args:
        return response.json({"error": "Profile not defined."}, status=404)

    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")

    for file in os.listdir(profiles_dir):
        if file.endswith(".json"):
            file_path = os.path.join(profiles_dir, file)
            memory = functions.GetVersionInfo(request)

            with open(file_path, "r") as f:
                profile = json.load(f)

            profile.setdefault("rvn", 0)
            profile.setdefault("items", {})
            profile.setdefault("stats", {})
            profile["stats"].setdefault("attributes", {})
            profile.setdefault("commandRevision", 0)

            if file == "athena.json":
                season_data_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Athena", "SeasonData.json")
                with open(season_data_path, "r") as f:
                    all_season_data = json.load(f)

                profile["stats"]["attributes"]["season_num"] = memory["season"]
                season_key = f"Season{memory['season']}"

                if season_key in all_season_data:
                    season_data = all_season_data[season_key]
                    attrs = profile["stats"]["attributes"]
                    attrs["book_purchased"] = season_data.get("battlePassPurchased", False)
                    attrs["book_level"] = season_data.get("battlePassTier", 0)
                    attrs["season_match_boost"] = season_data.get("battlePassXPBoost", 0)
                    attrs["season_friend_match_boost"] = season_data.get("battlePassXPFriendBoost", 0)

                with open(file_path, "w") as f:
                    json.dump(profile, f, indent=2)


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/SetAffiliateName")
async def set_affiliate_name(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, "common_core.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    with open(os.path.join(os.path.dirname(__file__), "..", "responses", "SAC.json"), "r") as f:
        supported_codes = json.load(f)

    body = request.json or {}
    affiliate_name = (body.get("affiliateName") or "").lower()

    for code in supported_codes:
        if affiliate_name == code.lower() or affiliate_name == "":
            profile["stats"]["attributes"]["mtx_affiliate_set_time"] = datetime.utcnow().isoformat() + "Z"
            profile["stats"]["attributes"]["mtx_affiliate"] = body.get("affiliateName", "")
            stat_changed = True
            break

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.extend([
            {
                "changeType": "statModified",
                "name": "mtx_affiliate_set_time",
                "value": profile["stats"]["attributes"]["mtx_affiliate_set_time"]
            },
            {
                "changeType": "statModified",
                "name": "mtx_affiliate",
                "value": profile["stats"]["attributes"]["mtx_affiliate"]
            }
        ])

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": "common_core",
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/<path:path>/client/SetHomebaseBanner")
async def set_homebase_banner(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_id = request.args.get("profileId", "profile0")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}
    icon_id = body.get("homebaseBannerIconId")
    color_id = body.get("homebaseBannerColorId")

    if icon_id and color_id:
        if profile_id == "profile0":
            profile["stats"]["attributes"]["homebase"]["bannerIconId"] = icon_id
            profile["stats"]["attributes"]["homebase"]["bannerColorId"] = color_id
            stat_changed = True

        elif profile_id == "common_public":
            profile["stats"]["attributes"]["banner_icon"] = icon_id
            profile["stats"]["attributes"]["banner_color"] = color_id
            stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        if profile_id == "profile0":
            apply_profile_changes.append({
                "changeType": "statModified",
                "name": "homebase",
                "value": profile["stats"]["attributes"]["homebase"]
            })
        elif profile_id == "common_public":
            apply_profile_changes.append({
                "changeType": "statModified",
                "name": "banner_icon",
                "value": profile["stats"]["attributes"]["banner_icon"]
            })
            apply_profile_changes.append({
                "changeType": "statModified",
                "name": "banner_color",
                "value": profile["stats"]["attributes"]["banner_color"]
            })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/<path:path>/client/SetHomebaseName")
async def set_homebase_name(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_id = request.args.get("profileId", "profile0")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}
    homebase_name = body.get("homebaseName")

    if homebase_name:
        if profile_id == "profile0":
            profile["stats"]["attributes"]["homebase"]["townName"] = homebase_name
            stat_changed = True

        elif profile_id == "common_public":
            profile["stats"]["attributes"]["homebase_name"] = homebase_name
            stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        if profile_id == "profile0":
            apply_profile_changes.append({
                "changeType": "statModified",
                "name": "homebase",
                "value": profile["stats"]["attributes"]["homebase"]
            })
        elif profile_id == "common_public":
            apply_profile_changes.append({
                "changeType": "statModified",
                "name": "homebase_name",
                "value": profile["stats"]["attributes"]["homebase_name"]
            })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/PurchaseHomebaseNode")
async def purchase_homebase_node(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_id = request.args.get("profileId", "profile0")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False
    item_id = None

    body = request.json or {}
    node_id = body.get("nodeId")

    if node_id:
        item_id = functions.MakeID()
        profile["items"][item_id] = {
            "templateId": f"HomebaseNode:{node_id}",
            "attributes": {"item_seen": True},
            "quantity": 1
        }
        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        apply_profile_changes.append({
            "changeType": "itemAdded",
            "itemId": item_id,
            "item": profile["items"][item_id]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile["rvn"],
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile["commandRevision"],
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/UnlockRewardNode")
async def unlock_reward_node(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_id = request.args.get("profileId", "athena")

    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")
    common_core_path = os.path.join(profiles_dir, "common_core.json")
    winterfest_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Athena", "winterfestRewards.json")

    profile = json.load(open(profile_path))
    common_core = json.load(open(common_core_path))
    winterfest_rewards = json.load(open(winterfest_path))

    memory = functions.GetVersionInfo(request)
    season_key = f"Season{memory['season']}"

    apply_profile_changes = []
    multi_update = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False
    common_core_changed = False
    item_exists = False

    gift_id = functions.MakeID()
    profile["items"][gift_id] = {
        "templateId": "GiftBox:gb_winterfestreward",
        "attributes": {
            "max_level_bonus": 0,
            "fromAccountId": "",
            "lootList": [],
            "level": 1,
            "item_seen": False,
            "xp": 0,
            "giftedOn": datetime.utcnow().isoformat(),
            "params": {"SubGame": "Athena", "winterfestGift": "true"},
            "favorite": False
        },
        "quantity": 1
    }

    body = request.json or {}
    node_id = body.get("nodeId")
    reward_graph_id = body.get("rewardGraphId")

    if node_id and reward_graph_id and season_key in winterfest_rewards:
        for reward in winterfest_rewards[season_key].get(node_id, []):
            item_id = functions.MakeID()
            item_exists = False

            if reward.lower().startswith("homebasebannericon:"):
                if not common_core_changed:
                    multi_update.append({
                        "profileRevision": common_core.get("rvn", 0),
                        "profileId": "common_core",
                        "profileChangesBaseRevision": common_core.get("rvn", 0),
                        "profileChanges": [],
                        "profileCommandRevision": common_core.get("commandRevision", 0)
                    })
                    common_core_changed = True

                for key, item in common_core["items"].items():
                    if item["templateId"].lower() == reward.lower():
                        item["attributes"]["item_seen"] = False
                        item_id = key
                        item_exists = True
                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemAttrChanged",
                            "itemId": key,
                            "attributeName": "item_seen",
                            "attributeValue": False
                        })

                if not item_exists:
                    common_core["items"][item_id] = {
                        "templateId": reward,
                        "attributes": {
                            "max_level_bonus": 0,
                            "level": 1,
                            "item_seen": False,
                            "xp": 0,
                            "variants": [],
                            "favorite": False
                        },
                        "quantity": 1
                    }
                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": common_core["items"][item_id]
                    })

                common_core["rvn"] += 1
                common_core["commandRevision"] += 1
                multi_update[0]["profileRevision"] = common_core["rvn"]
                multi_update[0]["profileCommandRevision"] = common_core["commandRevision"]

                profile["items"][gift_id]["attributes"]["lootList"].append({
                    "itemType": reward,
                    "itemGuid": item_id,
                    "itemProfile": "common_core",
                    "attributes": {"creation_time": datetime.utcnow().isoformat()},
                    "quantity": 1
                })

            else:
                for key, item in profile["items"].items():
                    if item["templateId"].lower() == reward.lower():
                        item["attributes"]["item_seen"] = False
                        item_id = key
                        item_exists = True
                        apply_profile_changes.append({
                            "changeType": "itemAttrChanged",
                            "itemId": key,
                            "attributeName": "item_seen",
                            "attributeValue": False
                        })

                if not item_exists:
                    profile["items"][item_id] = {
                        "templateId": reward,
                        "attributes": {
                            "max_level_bonus": 0,
                            "level": 1,
                            "item_seen": False,
                            "xp": 0,
                            "variants": [],
                            "favorite": False
                        },
                        "quantity": 1
                    }
                    apply_profile_changes.append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": profile["items"][item_id]
                    })

                profile["items"][gift_id]["attributes"]["lootList"].append({
                    "itemType": reward,
                    "itemGuid": item_id,
                    "itemProfile": "athena",
                    "attributes": {"creation_time": datetime.utcnow().isoformat()},
                    "quantity": 1
                })

        profile["items"][reward_graph_id]["attributes"]["reward_keys"][0]["unlock_keys_used"] += 1
        profile["items"][reward_graph_id]["attributes"]["reward_nodes_claimed"].append(node_id)
        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        apply_profile_changes.append({
            "changeType": "itemAdded",
            "itemId": gift_id,
            "item": profile["items"][gift_id]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        if common_core_changed:
            with open(common_core_path, "w") as f:
                json.dump(common_core, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile["rvn"],
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile["commandRevision"],
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "multiUpdate": multi_update,
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/RemoveGiftBox")
async def remove_gift_box(request, path):
    profile_id = request.args.get("profileId", "athena")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "giftBoxItemId" in body:
        id_ = body["giftBoxItemId"]
        profile["items"].pop(id_, None)
        apply_profile_changes.append({"changeType": "itemRemoved", "itemId": id_})
        stat_changed = True

    if "giftBoxItemIds" in body:
        for id_ in body["giftBoxItemIds"]:
            profile["items"].pop(id_, None)
            apply_profile_changes.append({"changeType": "itemRemoved", "itemId": id_})
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{"changeType": "fullProfileUpdate", "profile": profile}]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/SetPartyAssistQuest")
async def set_party_assist_quest(request, path):
    profile_id = request.args.get("profileId", "athena")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "party_assist_quest" in profile.get("stats", {}).get("attributes", {}):
        profile["stats"]["attributes"]["party_assist_quest"] = body.get("questToPinAsPartyAssist", "")
        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "party_assist_quest",
            "value": profile["stats"]["attributes"]["party_assist_quest"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{"changeType": "fullProfileUpdate", "profile": profile}]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/AthenaPinQuest")
async def athena_pin_quest(request, path):
    profile_id = request.args.get("profileId", "athena")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "pinned_quest" in profile.get("stats", {}).get("attributes", {}):
        profile["stats"]["attributes"]["pinned_quest"] = body.get("pinnedQuest", "")
        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "pinned_quest",
            "value": profile["stats"]["attributes"]["pinned_quest"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{"changeType": "fullProfileUpdate", "profile": profile}]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/SetPinnedQuests")
async def set_pinned_quests(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "pinnedQuestIds" in body:
        profile["stats"]["attributes"]["client_settings"]["pinnedQuestInstances"] = body["pinnedQuestIds"]
        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "client_settings",
            "value": profile["stats"]["attributes"]["client_settings"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{"changeType": "fullProfileUpdate", "profile": profile}]

    return response.json({
        "profileRevision": profile["rvn"],
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile["commandRevision"],
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/FortRerollDailyQuest")
async def fort_reroll_daily_quest(request, path):
    profile_id = request.args.get("profileId", "athena")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    if profile_id in ["profile0", "campaign"]:
        daily_quest_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Campaign", "quests.json")
    else:
        daily_quest_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Athena", "quests.json")

    with open(daily_quest_path, "r") as f:
        daily_quest_data = json.load(f)

    daily_quest_ids = daily_quest_data["Daily"]
    new_quest_id = functions.MakeID()
    random_index = random.randint(0, len(daily_quest_ids) - 1)

    
    existing_ids = [item["templateId"].lower() for item in profile["items"].values()]
    while daily_quest_ids[random_index]["templateId"].lower() in existing_ids:
        random_index = random.randint(0, len(daily_quest_ids) - 1)

    body = request.json or {}
    if "questId" in body and profile["stats"]["attributes"]["quest_manager"].get("dailyQuestRerolls", 0) >= 1:
        profile["stats"]["attributes"]["quest_manager"]["dailyQuestRerolls"] -= 1
        quest_id = body["questId"]

        profile["items"].pop(quest_id, None)

        selected_quest = daily_quest_ids[random_index]
        profile["items"][new_quest_id] = {
            "templateId": selected_quest["templateId"],
            "attributes": {
                "creation_time": datetime.utcnow().isoformat() + "Z",
                "level": -1,
                "item_seen": False,
                "sent_new_notification": False,
                "xp_reward_scalar": 1,
                "quest_state": "Active",
                "last_state_change_time": datetime.utcnow().isoformat() + "Z",
                "max_level_bonus": 0,
                "xp": 0,
                "favorite": False
            },
            "quantity": 1
        }

        for obj in selected_quest.get("objectives", []):
            profile["items"][new_quest_id]["attributes"][f"completion_{obj.lower()}"] = 0

        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        apply_profile_changes.extend([
            {
                "changeType": "statModified",
                "name": "quest_manager",
                "value": profile["stats"]["attributes"]["quest_manager"]
            },
            {
                "changeType": "itemAdded",
                "itemId": new_quest_id,
                "item": profile["items"][new_quest_id]
            },
            {
                "changeType": "itemRemoved",
                "itemId": body.get("questId")
            }
        ])

        notifications.append({
            "type": "dailyQuestReroll",
            "primary": True,
            "newQuestId": daily_quest_ids[random_index]["templateId"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{"changeType": "fullProfileUpdate", "profile": profile}]

    return response.json({
        "profileRevision": profile["rvn"],
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile["commandRevision"],
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/MarkNewQuestNotificationSent")
async def mark_new_quest_notification_sent(request, path):
    profile_id = request.args.get("profileId", "athena")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "itemIds" in body:
        for id_ in body["itemIds"]:
            if id_ in profile["items"]:
                profile["items"][id_]["attributes"]["sent_new_notification"] = True
                apply_profile_changes.append({
                    "changeType": "itemAttrChanged",
                    "itemId": id_,
                    "attributeName": "sent_new_notification",
                    "attributeValue": True
                })
        stat_changed = True

    if stat_changed:
        profile["rvn"] += 1
        profile["commandRevision"] += 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{"changeType": "fullProfileUpdate", "profile": profile}]

    return response.json({
        "profileRevision": profile["rvn"],
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile["commandRevision"],
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ClientQuestLogin")
async def client_quest_login(request, path):
    profile_id = request.args.get("profileId", "athena")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    athena_quests_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Athena", "quests.json")
    campaign_quests_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Campaign", "quests.json")
    
    with open(athena_quests_path, "r") as f:
        athena_quest_ids = json.load(f)
    
    with open(campaign_quests_path, "r") as f:
        campaign_quest_ids = json.load(f)

    memory = functions.GetVersionInfo(request)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    quest_count = 0
    should_give_quest = True
    date_format = datetime.utcnow().date().isoformat()
    daily_quest_ids = None
    season_quest_ids = None

    season_prefix = f"0{memory['season']}" if memory['season'] < 10 else str(memory['season'])

    try:
        if profile_id in ["profile0", "campaign"]:
            daily_quest_ids = campaign_quest_ids["Daily"]

            if f"Season{season_prefix}" in campaign_quest_ids:
                season_quest_ids = campaign_quest_ids[f"Season{season_prefix}"]

            for key, item in profile["items"].items():
                if item["templateId"].lower().startswith("quest:daily"):
                    quest_count += 1

            
            if config.getboolean("Profile", "bGrantFoundersPacks", fallback=False):
                quests_to_grant = [
                    "Quest:foundersquest_getrewards_0_1",
                    "Quest:foundersquest_getrewards_1_2",
                    "Quest:foundersquest_getrewards_2_3",
                    "Quest:foundersquest_getrewards_3_4",
                    "Quest:foundersquest_chooseherobundle",
                    "Quest:foundersquest_getrewards_4_5",
                    "Quest:foundersquest_herobundle_nochoice"
                ]

                for quest_template in quests_to_grant:
                    skip_this_quest = False
                    for key, item in profile["items"].items():
                        if item["templateId"].lower() == quest_template.lower():
                            skip_this_quest = True
                            break
                    if skip_this_quest:
                        continue

                    item_id = functions.MakeID()
                    item = {
                        "templateId": quest_template,
                        "attributes": {
                            "creation_time": "min",
                            "quest_state": "Completed",
                            "last_state_change_time": datetime.utcnow().isoformat() + "Z",
                            "level": -1,
                            "sent_new_notification": True,
                            "xp_reward_scalar": 1
                        },
                        "quantity": 1
                    }
                    profile["items"][item_id] = item
                    apply_profile_changes.append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": item
                    })
                    stat_changed = True

        if profile_id == "athena":
            daily_quest_ids = athena_quest_ids["Daily"]

            if f"Season{season_prefix}" in athena_quest_ids:
                season_quest_ids = athena_quest_ids[f"Season{season_prefix}"]

            for key, item in profile["items"].items():
                if item["templateId"].lower().startswith("quest:athenadaily"):
                    quest_count += 1

        if "quest_manager" in profile.get("stats", {}).get("attributes", {}):
            quest_manager = profile["stats"]["attributes"]["quest_manager"]
            if "dailyLoginInterval" in quest_manager:
                if "T" in quest_manager["dailyLoginInterval"]:
                    daily_login_date = quest_manager["dailyLoginInterval"].split("T")[0]

                    if daily_login_date == date_format:
                        should_give_quest = False
                    else:
                        should_give_quest = True
                        if quest_manager.get("dailyQuestRerolls", 0) <= 0:
                            quest_manager["dailyQuestRerolls"] += 1

        if quest_count < 3 and should_give_quest and daily_quest_ids:
            new_quest_id = functions.MakeID()
            random_number = random.randint(0, len(daily_quest_ids) - 1)

            
            existing_ids = [item["templateId"].lower() for item in profile["items"].values()]
            while daily_quest_ids[random_number]["templateId"].lower() in existing_ids:
                random_number = random.randint(0, len(daily_quest_ids) - 1)

            selected_quest = daily_quest_ids[random_number]
            profile["items"][new_quest_id] = {
                "templateId": selected_quest["templateId"],
                "attributes": {
                    "creation_time": datetime.utcnow().isoformat() + "Z",
                    "level": -1,
                    "item_seen": False,
                    "sent_new_notification": False,
                    "xp_reward_scalar": 1,
                    "quest_state": "Active",
                    "last_state_change_time": datetime.utcnow().isoformat() + "Z",
                    "max_level_bonus": 0,
                    "xp": 0,
                    "favorite": False
                },
                "quantity": 1
            }

            for objective in selected_quest.get("objectives", []):
                profile["items"][new_quest_id]["attributes"][f"completion_{objective.lower()}"] = 0

            profile["stats"]["attributes"]["quest_manager"]["dailyLoginInterval"] = datetime.utcnow().isoformat() + "Z"

            apply_profile_changes.extend([
                {
                    "changeType": "itemAdded",
                    "itemId": new_quest_id,
                    "item": profile["items"][new_quest_id]
                },
                {
                    "changeType": "statModified",
                    "name": "quest_manager",
                    "value": profile["stats"]["attributes"]["quest_manager"]
                }
            ])

            stat_changed = True

    except Exception as e:
        print(f"Error in ClientQuestLogin: {e}")

    
    for key in list(profile["items"].keys()):
        if (key.startswith("QS") and key[2:4].isdigit() and len(key) >= 5 and key[4] == "-"):
            if not key.startswith(f"QS{season_prefix}-"):
                del profile["items"][key]
                apply_profile_changes.append({
                    "changeType": "itemRemoved",
                    "itemId": key
                })
                stat_changed = True

    
    if season_quest_ids:
        quests_to_add = []
        
        if profile_id == "athena" and "ChallengeBundleSchedules" in season_quest_ids:
            for challenge_bundle_schedule_id, challenge_bundle_schedule in season_quest_ids["ChallengeBundleSchedules"].items():
                if challenge_bundle_schedule_id in profile["items"]:
                    apply_profile_changes.append({
                        "changeType": "itemRemoved",
                        "itemId": challenge_bundle_schedule_id
                    })

                profile["items"][challenge_bundle_schedule_id] = {
                    "templateId": challenge_bundle_schedule["templateId"],
                    "attributes": {
                        "unlock_epoch": datetime.utcnow().isoformat() + "Z",
                        "max_level_bonus": 0,
                        "level": 1,
                        "item_seen": True,
                        "xp": 0,
                        "favorite": False,
                        "granted_bundles": challenge_bundle_schedule["granted_bundles"]
                    },
                    "quantity": 1
                }

                apply_profile_changes.append({
                    "changeType": "itemAdded",
                    "itemId": challenge_bundle_schedule_id,
                    "item": profile["items"][challenge_bundle_schedule_id]
                })

                stat_changed = True

            if "ChallengeBundles" in season_quest_ids:
                for challenge_bundle_id, challenge_bundle in season_quest_ids["ChallengeBundles"].items():
                    if challenge_bundle_id in profile["items"]:
                        apply_profile_changes.append({
                            "changeType": "itemRemoved",
                            "itemId": challenge_bundle_id
                        })

                    if config.getboolean("Profile", "bCompletedSeasonalQuests", fallback=False) and "questStages" in challenge_bundle:
                        challenge_bundle["grantedquestinstanceids"] = challenge_bundle.get("grantedquestinstanceids", []) + challenge_bundle["questStages"]

                    profile["items"][challenge_bundle_id] = {
                        "templateId": challenge_bundle["templateId"],
                        "attributes": {
                            "has_unlock_by_completion": False,
                            "num_quests_completed": 0,
                            "level": 0,
                            "grantedquestinstanceids": challenge_bundle.get("grantedquestinstanceids", []),
                            "item_seen": True,
                            "max_allowed_bundle_level": 0,
                            "num_granted_bundle_quests": len(challenge_bundle.get("grantedquestinstanceids", [])),
                            "max_level_bonus": 0,
                            "challenge_bundle_schedule_id": challenge_bundle.get("challenge_bundle_schedule_id", ""),
                            "num_progress_quests_completed": 0,
                            "xp": 0,
                            "favorite": False
                        },
                        "quantity": 1
                    }

                    quests_to_add.extend(challenge_bundle.get("grantedquestinstanceids", []))

                    if config.getboolean("Profile", "bCompletedSeasonalQuests", fallback=False):
                        profile["items"][challenge_bundle_id]["attributes"]["num_quests_completed"] = len(challenge_bundle.get("grantedquestinstanceids", []))
                        profile["items"][challenge_bundle_id]["attributes"]["num_progress_quests_completed"] = len(challenge_bundle.get("grantedquestinstanceids", []))

                        if memory['season'] in [10, 11] and ("missionbundle_s10_0" in challenge_bundle["templateId"].lower() or challenge_bundle["templateId"].lower() == "challengebundle:missionbundle_s11_stretchgoals2"):
                            profile["items"][challenge_bundle_id]["attributes"]["level"] += 1

                    apply_profile_changes.append({
                        "changeType": "itemAdded",
                        "itemId": challenge_bundle_id,
                        "item": profile["items"][challenge_bundle_id]
                    })

                    stat_changed = True
        else:
            
            if "Quests" in season_quest_ids:
                quests_to_add = list(season_quest_ids["Quests"].keys())

        def parse_quest(quest_id):
            if quest_id not in season_quest_ids.get("Quests", {}):
                return
                
            quest = season_quest_ids["Quests"][quest_id]

            if quest_id in profile["items"]:
                apply_profile_changes.append({
                    "changeType": "itemRemoved",
                    "itemId": quest_id
                })

            profile["items"][quest_id] = {
                "templateId": quest["templateId"],
                "attributes": {
                    "creation_time": datetime.utcnow().isoformat() + "Z",
                    "level": -1,
                    "item_seen": True,
                    "sent_new_notification": True,
                    "challenge_bundle_id": quest.get("challenge_bundle_id", ""),
                    "xp_reward_scalar": 1,
                    "quest_state": "Active",
                    "last_state_change_time": datetime.utcnow().isoformat() + "Z",
                    "max_level_bonus": 0,
                    "xp": 0,
                    "favorite": False
                },
                "quantity": 1
            }

            if config.getboolean("Profile", "bCompletedSeasonalQuests", fallback=False):
                profile["items"][quest_id]["attributes"]["quest_state"] = "Claimed"

                if "rewards" in quest:
                    for reward in quest["rewards"]:
                        if reward["templateId"].startswith("Quest:"):
                            for q_id, q_data in season_quest_ids.get("Quests", {}).items():
                                if q_data["templateId"] == reward["templateId"]:
                                    challenge_bundle_id = q_data.get("challenge_bundle_id")
                                    if challenge_bundle_id and challenge_bundle_id in season_quest_ids.get("ChallengeBundles", {}):
                                        if q_id not in season_quest_ids["ChallengeBundles"][challenge_bundle_id].get("grantedquestinstanceids", []):
                                            season_quest_ids["ChallengeBundles"][challenge_bundle_id]["grantedquestinstanceids"].append(q_id)
                                    parse_quest(q_id)

            for i, objective in enumerate(quest.get("objectives", [])):
                attr_name = f"completion_{i}"
                if config.getboolean("Profile", "bCompletedSeasonalQuests", fallback=False):
                    profile["items"][quest_id]["attributes"][attr_name] = objective
                else:
                    profile["items"][quest_id]["attributes"][attr_name] = 0

            apply_profile_changes.append({
                "changeType": "itemAdded",
                "itemId": quest_id,
                "item": profile["items"][quest_id]
            })

            nonlocal stat_changed
            stat_changed = True

        for quest_id in quests_to_add:
            parse_quest(quest_id)

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/RefundItem")
async def refund_item(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        target_item_id = body["targetItemId"]
        item = profile["items"][target_item_id]
        
        
        item["templateId"] = item["templateId"][:-1] + "1"
        item["attributes"]["level"] = 1
        item["attributes"]["refundable"] = False

        
        new_item_id = functions.MakeID()
        profile["items"][new_item_id] = item
        
        
        del profile["items"][target_item_id]

        apply_profile_changes.extend([
            {
                "changeType": "itemAdded",
                "itemId": new_item_id,
                "item": profile["items"][new_item_id]
            },
            {
                "changeType": "itemRemoved",
                "itemId": target_item_id
            }
        ])

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/RefundMtxPurchase")
async def refund_mtx_purchase(request, path):
    profile_id = request.args.get("profileId", "common_core")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")
    item_profile_path = os.path.join(profiles_dir, "athena.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)
    
    with open(item_profile_path, "r") as f:
        item_profile = json.load(f)

    apply_profile_changes = []
    multi_update = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    item_guids = []

    body = request.json or {}
    
    if "purchaseId" in body:
        multi_update.append({
            "profileRevision": item_profile.get("rvn", 0),
            "profileId": "athena",
            "profileChangesBaseRevision": item_profile.get("rvn", 0),
            "profileChanges": [],
            "profileCommandRevision": item_profile.get("commandRevision", 0),
        })

        
        profile["stats"]["attributes"]["mtx_purchase_history"]["refundsUsed"] += 1
        profile["stats"]["attributes"]["mtx_purchase_history"]["refundCredits"] -= 1

        
        for purchase in profile["stats"]["attributes"]["mtx_purchase_history"]["purchases"]:
            if purchase["purchaseId"] == body["purchaseId"]:
                
                for loot_result in purchase.get("lootResult", []):
                    if "itemGuid" in loot_result:
                        item_guids.append(loot_result["itemGuid"])

                
                purchase["refundDate"] = datetime.utcnow().isoformat() + "Z"

                
                for key, item in profile["items"].items():
                    if item["templateId"].lower().startswith("currency:mtx"):
                        current_platform = profile["stats"]["attributes"].get("current_mtx_platform", "").lower()
                        item_platform = item["attributes"].get("platform", "").lower()
                        
                        if item_platform == current_platform or item_platform == "shared":
                            item["quantity"] += purchase.get("totalMtxPaid", 0)
                            
                            apply_profile_changes.append({
                                "changeType": "itemQuantityChanged",
                                "itemId": key,
                                "quantity": item["quantity"]
                            })
                            break

        
        for item_guid in item_guids:
            if item_guid in item_profile["items"]:
                del item_profile["items"][item_guid]
                
                multi_update[0]["profileChanges"].append({
                    "changeType": "itemRemoved",
                    "itemId": item_guid
                })

        
        item_profile["rvn"] = item_profile.get("rvn", 0) + 1
        item_profile["commandRevision"] = item_profile.get("commandRevision", 0) + 1
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        stat_changed = True

    if stat_changed:
        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "mtx_purchase_history",
            "value": profile["stats"]["attributes"]["mtx_purchase_history"]
        })

        multi_update[0]["profileRevision"] = item_profile.get("rvn", 0)
        multi_update[0]["profileCommandRevision"] = item_profile.get("commandRevision", 0)

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
        
        with open(item_profile_path, "w") as f:
            json.dump(item_profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "multiUpdate": multi_update,
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/IncrementNamedCounterStat")
async def increment_named_counter_stat(request, path):
    profile_id = request.args.get("profileId", "profile0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "counterName" in body and "named_counters" in profile.get("stats", {}).get("attributes", {}):
        counter_name = body["counterName"]
        named_counters = profile["stats"]["attributes"]["named_counters"]
        
        if counter_name in named_counters:
            named_counters[counter_name]["current_count"] += 1
            named_counters[counter_name]["last_incremented_time"] = datetime.utcnow().isoformat() + "Z"
            stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "named_counters",
            "value": profile["stats"]["attributes"]["named_counters"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ClaimLoginReward")
async def claim_login_reward(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")
    
    daily_rewards_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Campaign", "dailyRewards.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)
    
    with open(daily_rewards_path, "r") as f:
        daily_rewards = json.load(f)

    memory = functions.GetVersionInfo(request)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    date_format = datetime.utcnow().date().isoformat() + "T00:00:00.000Z"

    daily_rewards_attrs = profile["stats"]["attributes"].get("daily_rewards", {})
    
    if daily_rewards_attrs.get("lastClaimDate") != date_format:
        daily_rewards_attrs["nextDefaultReward"] += 1
        daily_rewards_attrs["totalDaysLoggedIn"] += 1
        daily_rewards_attrs["lastClaimDate"] = date_format
        
        if "additionalSchedules" in daily_rewards_attrs and "founderspackdailyrewardtoken" in daily_rewards_attrs["additionalSchedules"]:
            daily_rewards_attrs["additionalSchedules"]["founderspackdailyrewardtoken"]["rewardsClaimed"] += 1
        
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "daily_rewards",
            "value": daily_rewards_attrs
        })

        if memory["season"] < 7:
            day = daily_rewards_attrs["totalDaysLoggedIn"] % 336
            if day < len(daily_rewards):
                notifications.append({
                    "type": "daily_rewards",
                    "primary": True,
                    "daysLoggedIn": daily_rewards_attrs["totalDaysLoggedIn"],
                    "items": [daily_rewards[day]]
                })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/UpdateQuestClientObjectives")
async def update_quest_client_objectives(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "advance" in body:
        for advance_item in body["advance"]:
            quests_to_update = []

            
            for item_id, item in profile["items"].items():
                if item["templateId"].lower().startswith("quest:"):
                    for attr_name in item["attributes"]:
                        if attr_name.lower() == f"completion_{advance_item['statName']}".lower():
                            quests_to_update.append(item_id)
                            break

            
            for quest_id in quests_to_update:
                incomplete = False
                
                
                attr_name = f"completion_{advance_item['statName']}"
                profile["items"][quest_id]["attributes"][attr_name] = advance_item["count"]

                apply_profile_changes.append({
                    "changeType": "itemAttrChanged",
                    "itemId": quest_id,
                    "attributeName": attr_name,
                    "attributeValue": advance_item["count"]
                })

                
                if profile["items"][quest_id]["attributes"]["quest_state"].lower() != "claimed":
                    for attr_name, attr_value in profile["items"][quest_id]["attributes"].items():
                        if attr_name.lower().startswith("completion_") and attr_value == 0:
                            incomplete = True
                            break

                    if not incomplete:
                        profile["items"][quest_id]["attributes"]["quest_state"] = "Claimed"

                        apply_profile_changes.append({
                            "changeType": "itemAttrChanged",
                            "itemId": quest_id,
                            "attributeName": "quest_state",
                            "attributeValue": "Claimed"
                        })

                stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/AssignTeamPerkToLoadout")
async def assign_team_perk_to_loadout(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, "campaign.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "loadoutId" in body and body["loadoutId"] in profile["items"]:
        profile["items"][body["loadoutId"]]["attributes"]["team_perk"] = body.get("teamPerkId", "")
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["loadoutId"],
            "attributeName": "team_perk",
            "attributeValue": profile["items"][body["loadoutId"]]["attributes"]["team_perk"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": "campaign",
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/AssignGadgetToLoadout")
async def assign_gadget_to_loadout(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, "campaign.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "loadoutId" in body and body["loadoutId"] in profile["items"]:
        slot_index = body.get("slotIndex")
        gadget_id = body.get("gadgetId", "")

        if slot_index in [0, 1]:
            gadgets = profile["items"][body["loadoutId"]]["attributes"]["gadgets"]
            
            if slot_index == 0:
                if gadget_id.lower() == gadgets[1]["gadget"].lower():
                    gadgets[1]["gadget"] = ""
                gadgets[0]["gadget"] = gadget_id
                stat_changed = True
            elif slot_index == 1:
                if gadget_id.lower() == gadgets[0]["gadget"].lower():
                    gadgets[0]["gadget"] = ""
                gadgets[1]["gadget"] = gadget_id
                stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["loadoutId"],
            "attributeName": "gadgets",
            "attributeValue": profile["items"][body["loadoutId"]]["attributes"]["gadgets"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": "campaign",
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/AssignWorkerToSquad")
async def assign_worker_to_squad(request, path):
    profile_id = request.args.get("profileId", "profile0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "characterId" in body:
        
        for item_id, item in profile["items"].items():
            if "attributes" in item:
                attrs = item["attributes"]
                if "squad_id" in attrs and "squad_slot_idx" in attrs:
                    if (attrs["squad_id"] != "" and attrs["squad_slot_idx"] != -1 and
                        attrs["squad_id"].lower() == body.get("squadId", "").lower() and 
                        attrs["squad_slot_idx"] == body.get("slotIndex")):
                        
                        attrs["squad_id"] = ""
                        attrs["squad_slot_idx"] = 0

                        apply_profile_changes.extend([
                            {
                                "changeType": "itemAttrChanged",
                                "itemId": item_id,
                                "attributeName": "squad_id",
                                "attributeValue": attrs["squad_id"]
                            },
                            {
                                "changeType": "itemAttrChanged",
                                "itemId": item_id,
                                "attributeName": "squad_slot_idx",
                                "attributeValue": attrs["squad_slot_idx"]
                            }
                        ])

        
        character_id = body["characterId"]
        if character_id in profile["items"]:
            profile["items"][character_id]["attributes"]["squad_id"] = body.get("squadId", "")
            profile["items"][character_id]["attributes"]["squad_slot_idx"] = body.get("slotIndex", 0)
            stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.extend([
            {
                "changeType": "itemAttrChanged",
                "itemId": body["characterId"],
                "attributeName": "squad_id",
                "attributeValue": profile["items"][body["characterId"]]["attributes"]["squad_id"]
            },
            {
                "changeType": "itemAttrChanged",
                "itemId": body["characterId"],
                "attributeName": "squad_slot_idx",
                "attributeValue": profile["items"][body["characterId"]]["attributes"]["squad_slot_idx"]
            }
        ])

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/AssignWorkerToSquadBatch")
async def assign_worker_to_squad_batch(request, path):
    profile_id = request.args.get("profileId", "profile0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if all(key in body for key in ["characterIds", "squadIds", "slotIndices"]):
        character_ids = body["characterIds"]
        squad_ids = body["squadIds"]
        slot_indices = body["slotIndices"]

        for i in range(len(character_ids)):
            
            for item_id, item in profile["items"].items():
                if "attributes" in item:
                    attrs = item["attributes"]
                    if "squad_id" in attrs and "squad_slot_idx" in attrs:
                        if (attrs["squad_id"] != "" and attrs["squad_slot_idx"] != -1 and
                            attrs["squad_id"].lower() == squad_ids[i].lower() and 
                            attrs["squad_slot_idx"] == slot_indices[i]):
                            
                            attrs["squad_id"] = ""
                            attrs["squad_slot_idx"] = 0

                            apply_profile_changes.extend([
                                {
                                    "changeType": "itemAttrChanged",
                                    "itemId": item_id,
                                    "attributeName": "squad_id",
                                    "attributeValue": attrs["squad_id"]
                                },
                                {
                                    "changeType": "itemAttrChanged",
                                    "itemId": item_id,
                                    "attributeName": "squad_slot_idx",
                                    "attributeValue": attrs["squad_slot_idx"]
                                }
                            ])

            
            character_id = character_ids[i]
            if character_id in profile["items"]:
                profile["items"][character_id]["attributes"]["squad_id"] = squad_ids[i]
                profile["items"][character_id]["attributes"]["squad_slot_idx"] = slot_indices[i]

                apply_profile_changes.extend([
                    {
                        "changeType": "itemAttrChanged",
                        "itemId": character_id,
                        "attributeName": "squad_id",
                        "attributeValue": profile["items"][character_id]["attributes"]["squad_id"]
                    },
                    {
                        "changeType": "itemAttrChanged",
                        "itemId": character_id,
                        "attributeName": "squad_slot_idx",
                        "attributeValue": profile["items"][character_id]["attributes"]["squad_slot_idx"]
                    }
                ])

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ClaimQuestReward")
async def claim_quest_reward(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")
    common_core_path = os.path.join(profiles_dir, "common_core.json")
    theater0_path = os.path.join(profiles_dir, "theater0.json")
    rewards_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Campaign", "rewards.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)
    
    with open(common_core_path, "r") as f:
        common_core = json.load(f)
    
    with open(theater0_path, "r") as f:
        theater0 = json.load(f)
    
    with open(rewards_path, "r") as f:
        rewards_data = json.load(f)

    rewards = rewards_data.get("quest", {})

    apply_profile_changes = []
    multi_update = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False
    theater_stat_changed = False
    common_core_stat_changed = False

    body = request.json or {}

    if "questId" in body:
        quest_template_id = None
        
        
        for key, item in profile["items"].items():
            if key.lower() == body["questId"].lower():
                quest_template_id = item["templateId"].lower()
                break

        if quest_template_id and quest_template_id in rewards:
            current_rewards = rewards[quest_template_id]
            
            
            if (body.get("selectedRewardIndex", -1) != -1 and 
                "selectableRewards" in current_rewards):
                selected_index = body["selectedRewardIndex"]
                if selected_index < len(current_rewards["selectableRewards"]):
                    current_rewards = current_rewards["selectableRewards"][selected_index]["rewards"]
            else:
                current_rewards = current_rewards["rewards"]

            
            multi_update.append({
                "profileRevision": theater0.get("rvn", 0),
                "profileId": "theater0",
                "profileChangesBaseRevision": theater0.get("rvn", 0),
                "profileChanges": [],
                "profileCommandRevision": theater0.get("commandRevision", 0),
            })

            
            if profile_id == "campaign":
                multi_update.append({
                    "profileRevision": common_core.get("rvn", 0),
                    "profileId": "common_core",
                    "profileChangesBaseRevision": common_core.get("rvn", 0),
                    "profileChanges": [],
                    "profileCommandRevision": common_core.get("commandRevision", 0),
                })

            notifications.append({
                "type": "questClaim",
                "primary": True,
                "questId": quest_template_id,
                "loot": {
                    "items": []
                }
            })

            
            for reward in current_rewards:
                item_id = functions.MakeID()
                template_id = reward["templateId"].lower()
                quantity = reward["quantity"]

                if template_id.startswith(("weapon:", "trap:", "ammo:")):
                    
                    item_data = {
                        "templateId": reward["templateId"],
                        "attributes": {
                            "clipSizeScale": 0,
                            "loadedAmmo": 999,
                            "level": 1,
                            "alterationDefinitions": [],
                            "baseClipSize": 999,
                            "durability": 375,
                            "itemSource": "",
                            "item_seen": False
                        },
                        "quantity": quantity
                    }
                    
                    theater0["items"][item_id] = item_data
                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": theater0["items"][item_id]
                    })

                    notifications[0]["loot"]["items"].append({
                        "itemType": reward["templateId"],
                        "itemGuid": item_id,
                        "itemProfile": "theater0",
                        "quantity": quantity
                    })

                    theater_stat_changed = True

                elif (profile_id == "campaign" and 
                      (template_id.startswith("homebasebannericon:") or 
                       template_id == "token:founderchatunlock")):
                    
                    item_data = {
                        "templateId": reward["templateId"],
                        "attributes": {
                            "max_level_bonus": 0,
                            "level": 1,
                            "item_seen": False,
                            "xp": 0,
                            "favorite": False
                        },
                        "quantity": quantity
                    }
                    
                    common_core["items"][item_id] = item_data
                    multi_update[1]["profileChanges"].append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": common_core["items"][item_id]
                    })

                    notifications[0]["loot"]["items"].append({
                        "itemType": reward["templateId"],
                        "itemGuid": item_id,
                        "itemProfile": "common_core",
                        "quantity": quantity
                    })

                    common_core_stat_changed = True

                else:
                    
                    item_data = {
                        "templateId": reward["templateId"],
                        "attributes": {
                            "legacy_alterations": [],
                            "max_level_bonus": 0,
                            "level": 1,
                            "refund_legacy_item": False,
                            "item_seen": False,
                            "alterations": ["", "", "", "", "", ""],
                            "xp": 0,
                            "refundable": False,
                            "alteration_base_rarities": [],
                            "favorite": False
                        },
                        "quantity": quantity
                    }
                    
                    
                    if template_id.startswith("quest:"):
                        item_data["attributes"]["quest_state"] = "Active"

                    profile["items"][item_id] = item_data
                    apply_profile_changes.append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": profile["items"][item_id]
                    })
                    
                    notifications[0]["loot"]["items"].append({
                        "itemType": reward["templateId"],
                        "itemGuid": item_id,
                        "itemProfile": profile_id,
                        "quantity": quantity
                    })

            
            profile["items"][body["questId"]]["attributes"]["quest_state"] = "Claimed"
            profile["items"][body["questId"]]["attributes"]["last_state_change_time"] = datetime.utcnow().isoformat() + "Z"
            stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        
        if theater_stat_changed:
            theater0["rvn"] = theater0.get("rvn", 0) + 1
            theater0["commandRevision"] = theater0.get("commandRevision", 0) + 1
            multi_update[0]["profileRevision"] = theater0["rvn"]
            multi_update[0]["profileCommandRevision"] = theater0["commandRevision"]

            with open(theater0_path, "w") as f:
                json.dump(theater0, f, indent=2)

        
        if common_core_stat_changed:
            common_core["rvn"] = common_core.get("rvn", 0) + 1
            common_core["commandRevision"] = common_core.get("commandRevision", 0) + 1
            multi_update[1]["profileRevision"] = common_core["rvn"]
            multi_update[1]["profileCommandRevision"] = common_core["commandRevision"]

            with open(common_core_path, "w") as f:
                json.dump(common_core, f, indent=2)

        
        apply_profile_changes.extend([
            {
                "changeType": "itemAttrChanged",
                "itemId": body["questId"],
                "attributeName": "quest_state",
                "attributeValue": profile["items"][body["questId"]]["attributes"]["quest_state"]
            },
            {
                "changeType": "itemAttrChanged",
                "itemId": body["questId"],
                "attributeName": "last_state_change_time",
                "attributeValue": profile["items"][body["questId"]]["attributes"]["last_state_change_time"]
            }
        ])

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "multiUpdate": multi_update,
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/UpgradeItem")
async def upgrade_item(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        profile["items"][body["targetItemId"]]["attributes"]["level"] += 1
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["targetItemId"],
            "attributeName": "level",
            "attributeValue": profile["items"][body["targetItemId"]]["attributes"]["level"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/UpgradeSlottedItem")
async def upgrade_slotted_item(request, path):
    profile_id = request.args.get("profileId", "collection_book_people0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        if "desiredLevel" in body:
            new_level = int(body["desiredLevel"])
            profile["items"][body["targetItemId"]]["attributes"]["level"] = new_level
        else:
            profile["items"][body["targetItemId"]]["attributes"]["level"] += 1
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["targetItemId"],
            "attributeName": "level",
            "attributeValue": profile["items"][body["targetItemId"]]["attributes"]["level"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/UpgradeItemBulk")
async def upgrade_item_bulk(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"] and "desiredLevel" in body:
        new_level = int(body["desiredLevel"])
        profile["items"][body["targetItemId"]]["attributes"]["level"] = new_level
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["targetItemId"],
            "attributeName": "level",
            "attributeValue": profile["items"][body["targetItemId"]]["attributes"]["level"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ConvertItem")
async def convert_item(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        item = profile["items"][body["targetItemId"]]
        template_id = item["templateId"].lower()

        
        if "t04" in template_id:
            item["templateId"] = item["templateId"].replace("t04", "T05").replace("T04", "T05")
        elif "t03" in template_id:
            item["templateId"] = item["templateId"].replace("t03", "T04").replace("T03", "T04")
        elif "t02" in template_id:
            item["templateId"] = item["templateId"].replace("t02", "T03").replace("T02", "T03")
        elif "t01" in template_id:
            item["templateId"] = item["templateId"].replace("t01", "T02").replace("T01", "T02")

        
        if body.get("conversionIndex") == 1:
            item["templateId"] = item["templateId"].replace("ore", "Crystal").replace("Ore", "Crystal")

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        
        new_item_id = functions.MakeID()
        profile["items"][new_item_id] = profile["items"][body["targetItemId"]]
        
        
        del profile["items"][body["targetItemId"]]

        apply_profile_changes.extend([
            {
                "changeType": "itemAdded",
                "itemId": new_item_id,
                "item": profile["items"][new_item_id]
            },
            {
                "changeType": "itemRemoved",
                "itemId": body["targetItemId"]
            }
        ])

        notifications.append({
            "type": "conversionResult",
            "primary": True,
            "itemsGranted": [
                {
                    "itemType": profile["items"][new_item_id]["templateId"],
                    "itemGuid": new_item_id,
                    "itemProfile": profile_id,
                    "attributes": {
                        "level": profile["items"][new_item_id]["attributes"].get("level", 1),
                        "alterations": profile["items"][new_item_id]["attributes"].get("alterations", [])
                    },
                    "quantity": 1
                }
            ]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ConvertSlottedItem")
async def convert_slotted_item(request, path):
    profile_id = request.args.get("profileId", "collection_book_people0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        item = profile["items"][body["targetItemId"]]
        template_id = item["templateId"].lower()

        
        if "t04" in template_id:
            item["templateId"] = item["templateId"].replace("t04", "T05").replace("T04", "T05")
        elif "t03" in template_id:
            item["templateId"] = item["templateId"].replace("t03", "T04").replace("T03", "T04")
        elif "t02" in template_id:
            item["templateId"] = item["templateId"].replace("t02", "T03").replace("T02", "T03")
        elif "t01" in template_id:
            item["templateId"] = item["templateId"].replace("t01", "T02").replace("T01", "T02")

        
        if body.get("conversionIndex") == 1:
            item["templateId"] = item["templateId"].replace("ore", "Crystal").replace("Ore", "Crystal")

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        
        new_item_id = functions.MakeID()
        profile["items"][new_item_id] = profile["items"][body["targetItemId"]]
        
        
        del profile["items"][body["targetItemId"]]

        apply_profile_changes.extend([
            {
                "changeType": "itemAdded",
                "itemId": new_item_id,
                "item": profile["items"][new_item_id]
            },
            {
                "changeType": "itemRemoved",
                "itemId": body["targetItemId"]
            }
        ])

        notifications.append({
            "type": "conversionResult",
            "primary": True,
            "itemsGranted": [
                {
                    "itemType": profile["items"][new_item_id]["templateId"],
                    "itemGuid": new_item_id,
                    "itemProfile": profile_id,
                    "attributes": {
                        "level": profile["items"][new_item_id]["attributes"].get("level", 1),
                        "alterations": profile["items"][new_item_id]["attributes"].get("alterations", [])
                    },
                    "quantity": 1
                }
            ]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/UpgradeItemRarity")
async def upgrade_item_rarity(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        item = profile["items"][body["targetItemId"]]
        template_id = item["templateId"].lower()

        
        if "_vr_" in template_id:
            item["templateId"] = item["templateId"].replace("_vr_", "_SR_").replace("_VR_", "_SR_")
        elif "_r_" in template_id:
            item["templateId"] = item["templateId"].replace("_r_", "_VR_").replace("_R_", "_VR_")
        elif "_uc_" in template_id:
            item["templateId"] = item["templateId"].replace("_uc_", "_R_").replace("_UC_", "_R_")
        elif "_c_" in template_id:
            item["templateId"] = item["templateId"].replace("_c_", "_UC_").replace("_C_", "_UC_")

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        
        new_item_id = functions.MakeID()
        profile["items"][new_item_id] = profile["items"][body["targetItemId"]]
        
        
        del profile["items"][body["targetItemId"]]

        apply_profile_changes.extend([
            {
                "changeType": "itemAdded",
                "itemId": new_item_id,
                "item": profile["items"][new_item_id]
            },
            {
                "changeType": "itemRemoved",
                "itemId": body["targetItemId"]
            }
        ])

        notifications.append([{
            "type": "upgradeItemRarityNotification",
            "primary": True,
            "itemsGranted": [
                {
                    "itemType": profile["items"][new_item_id]["templateId"],
                    "itemGuid": new_item_id,
                    "itemProfile": profile_id,
                    "attributes": {
                        "level": profile["items"][new_item_id]["attributes"].get("level", 1),
                        "alterations": profile["items"][new_item_id]["attributes"].get("alterations", [])
                    },
                    "quantity": 1
                }
            ]
        }])

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/PromoteItem")
async def promote_item(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemId" in body and body["targetItemId"] in profile["items"]:
        profile["items"][body["targetItemId"]]["attributes"]["level"] += 2
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["targetItemId"],
            "attributeName": "level",
            "attributeValue": profile["items"][body["targetItemId"]]["attributes"]["level"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/TransmogItem")
async def transmog_item(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")
    transform_item_ids_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Campaign", "transformItemIDS.json")
    card_pack_data_path = os.path.join(os.path.dirname(__file__), "..", "responses", "Campaign", "cardPackData.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)
    
    with open(transform_item_ids_path, "r") as f:
        transform_item_ids = json.load(f)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "sacrificeItemIds" in body and "transmogKeyTemplateId" in body:
        
        for item_id in body["sacrificeItemIds"]:
            if item_id in profile["items"]:
                del profile["items"][item_id]
                apply_profile_changes.append({
                    "changeType": "itemRemoved",
                    "itemId": item_id
                })

        
        if body["transmogKeyTemplateId"] in transform_item_ids:
            transform_items = transform_item_ids[body["transmogKeyTemplateId"]]
        else:
            with open(card_pack_data_path, "r") as f:
                card_pack_data = json.load(f)
            transform_items = card_pack_data["default"]

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        
        random_number = random.randint(0, len(transform_items) - 1)
        new_item_id = functions.MakeID()
        
        item_template = transform_items[random_number]
        item_data = {
            "templateId": item_template,
            "attributes": {
                "legacy_alterations": [],
                "max_level_bonus": 0,
                "level": 1,
                "refund_legacy_item": False,
                "item_seen": False,
                "alterations": ["", "", "", "", "", ""],
                "xp": 0,
                "refundable": False,
                "alteration_base_rarities": [],
                "favorite": False
            },
            "quantity": 1
        }

        
        if item_template.lower().startswith("worker:"):
            item_data["attributes"] = functions.MakeSurvivorAttributes(item_template)

        profile["items"][new_item_id] = item_data

        notifications.append({
            "type": "transmogResult",
            "primary": True,
            "transmoggedItems": [
                {
                    "itemType": profile["items"][new_item_id]["templateId"],
                    "itemGuid": new_item_id,
                    "itemProfile": profile_id,
                    "attributes": profile["items"][new_item_id]["attributes"],
                    "quantity": 1
                }
            ]
        })

        apply_profile_changes.append({
            "changeType": "itemAdded",
            "itemId": new_item_id,
            "item": item_data
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/CraftWorldItem")
async def craft_world_item(request, path):
    memory = functions.GetVersionInfo(request)
    profile_id = request.args.get("profileId", "theater0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")
    
    
    chosen_profile = False
    schematic_profile_path = None
    
    if memory["season"] >= 4 or memory["build"] in [3.5, 3.6]:
        schematic_profile_path = os.path.join(profiles_dir, "campaign.json")
        chosen_profile = True
    
    if memory["season"] <= 3 and not chosen_profile:
        schematic_profile_path = os.path.join(profiles_dir, "profile0.json")
        chosen_profile = True

    with open(profile_path, "r") as f:
        profile = json.load(f)
    
    with open(schematic_profile_path, "r") as f:
        schematic_profile = json.load(f)

    apply_profile_changes = []
    notifications = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetSchematicItemId" in body and body["targetSchematicItemId"] in schematic_profile["items"]:
        
        schematic_item = json.loads(json.dumps(schematic_profile["items"][body["targetSchematicItemId"]]))
        
        item_type = "Weapon:"
        item_id_type = "WID_"
        
        
        schematic_parts = schematic_item["templateId"].split("_")
        if len(schematic_parts) > 1:
            first_part = schematic_parts[1].split("_")[0].lower()
            if first_part in ["wall", "floor", "ceiling"]:
                item_type = "Trap:"
                item_id_type = "TID_"

        
        template_id_lower = schematic_item["templateId"].lower()
        
        
        if template_id_lower.startswith("schematic:sid_pistol_vacuumtube_auto_"):
            schematic_item["templateId"] = f"Schematic:SID_Pistol_Auto_VacuumTube_{schematic_item['templateId'][37:]}"
        
        
        if template_id_lower.startswith("schematic:sid_launcher_grenade_winter_"):
            schematic_item["templateId"] = f"Schematic:SID_Launcher_WinterGrenade_{schematic_item['templateId'][38:]}"

        
        schematic_item["templateId"] = schematic_item["templateId"].replace("Schematic:", item_type)
        schematic_item["templateId"] = schematic_item["templateId"].replace("SID_", item_id_type)
        schematic_item["quantity"] = body.get("numTimesToCraft", 1)

        
        if "targetSchematicTier" in body:
            tier = body["targetSchematicTier"].lower()
            current_template = schematic_item["templateId"]
            
            if tier == "i":
                if "t01" not in current_template.lower():
                    schematic_item["attributes"]["level"] = 10
                schematic_item["templateId"] = current_template[:-3] + "T01"
                schematic_item["templateId"] = schematic_item["templateId"].replace("_Crystal_", "_Ore_")
            
            elif tier == "ii":
                if "t02" not in current_template.lower():
                    schematic_item["attributes"]["level"] = 20
                schematic_item["templateId"] = current_template[:-3] + "T02"
                schematic_item["templateId"] = schematic_item["templateId"].replace("_Crystal_", "_Ore_")
            
            elif tier == "iii":
                if "t03" not in current_template.lower():
                    schematic_item["attributes"]["level"] = 30
                schematic_item["templateId"] = current_template[:-3] + "T03"
                schematic_item["templateId"] = schematic_item["templateId"].replace("_Crystal_", "_Ore_")
            
            elif tier == "iv":
                if "t04" not in current_template.lower():
                    schematic_item["attributes"]["level"] = 40
                schematic_item["templateId"] = current_template[:-3] + "T04"
            
            elif tier == "v":
                schematic_item["templateId"] = current_template[:-3] + "T05"

        
        schematic_item["attributes"] = {
            "clipSizeScale": 0,
            "loadedAmmo": 999,
            "level": schematic_item["attributes"].get("level", 1),
            "alterationDefinitions": schematic_item["attributes"].get("alterations", []),
            "baseClipSize": 999,
            "durability": 375,
            "itemSource": ""
        }

        
        new_item_id = functions.MakeID()
        profile["items"][new_item_id] = schematic_item
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAdded",
            "itemId": new_item_id,
            "item": profile["items"][new_item_id]
        })

        notifications.append({
            "type": "craftingResult",
            "primary": True,
            "itemsCrafted": [
                {
                    "itemType": profile["items"][new_item_id]["templateId"],
                    "itemGuid": new_item_id,
                    "itemProfile": profile_id,
                    "attributes": {
                        "loadedAmmo": profile["items"][new_item_id]["attributes"]["loadedAmmo"],
                        "level": profile["items"][new_item_id]["attributes"]["level"],
                        "alterationDefinitions": profile["items"][new_item_id]["attributes"]["alterationDefinitions"],
                        "durability": profile["items"][new_item_id]["attributes"]["durability"]
                    },
                    "quantity": profile["items"][new_item_id]["quantity"]
                }
            ]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "notifications": notifications,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/DestroyWorldItems")
async def destroy_world_items(request, path):
    profile_id = request.args.get("profileId", "theater0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "itemIds" in body:
        for item_id in body["itemIds"]:
            if item_id in profile["items"]:
                del profile["items"][item_id]
                apply_profile_changes.append({
                    "changeType": "itemRemoved",
                    "itemId": item_id
                })
                stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/DisassembleWorldItems")
async def disassemble_world_items(request, path):
    profile_id = request.args.get("profileId", "theater0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "targetItemIdAndQuantityPairs" in body:
        for item_pair in body["targetItemIdAndQuantityPairs"]:
            item_id = item_pair["itemId"]
            quantity = int(item_pair["quantity"])
            
            if item_id in profile["items"]:
                original_quantity = int(profile["items"][item_id]["quantity"])
                
                if quantity >= original_quantity:
                    
                    del profile["items"][item_id]
                    apply_profile_changes.append({
                        "changeType": "itemRemoved",
                        "itemId": item_id
                    })
                else:
                    
                    profile["items"][item_id]["quantity"] -= quantity
                    apply_profile_changes.append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": profile["items"][item_id]["quantity"]
                    })
                
                stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/StorageTransfer")
async def storage_transfer(request, path):
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    theater0_path = os.path.join(profiles_dir, "theater0.json")
    outpost0_path = os.path.join(profiles_dir, "outpost0.json")

    with open(theater0_path, "r") as f:
        theater0 = json.load(f)
    
    with open(outpost0_path, "r") as f:
        outpost0 = json.load(f)

    apply_profile_changes = []
    multi_update = []
    base_revision = theater0.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    def get_item_quantity(profile, item_id):
        return int(profile["items"].get(item_id, {}).get("quantity", 0)) if item_id in profile["items"] else "Unknown"

    if "transferOperations" in body:
        multi_update.append({
            "profileRevision": outpost0.get("rvn", 0),
            "profileId": "outpost0",
            "profileChangesBaseRevision": outpost0.get("rvn", 0),
            "profileChanges": [],
            "profileCommandRevision": outpost0.get("commandRevision", 0),
        })

        for operation in body["transferOperations"]:
            item_id = operation["itemId"]
            quantity = int(operation["quantity"])
            to_storage = operation.get("toStorage", False)

            theater_quantity = get_item_quantity(theater0, item_id)
            outpost_quantity = get_item_quantity(outpost0, item_id)

            if not to_storage:  
                if theater_quantity != "Unknown" and outpost_quantity != "Unknown":
                    if outpost_quantity > quantity:
                        theater0["items"][item_id]["quantity"] += quantity
                        outpost0["items"][item_id]["quantity"] -= quantity

                        apply_profile_changes.append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": theater0["items"][item_id]["quantity"]
                        })

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": outpost0["items"][item_id]["quantity"]
                        })
                    else:
                        theater0["items"][item_id]["quantity"] += outpost_quantity
                        del outpost0["items"][item_id]

                        apply_profile_changes.append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": theater0["items"][item_id]["quantity"]
                        })

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemRemoved",
                            "itemId": item_id
                        })
                elif theater_quantity == "Unknown" and outpost_quantity != "Unknown":
                    item_copy = json.loads(json.dumps(outpost0["items"][item_id]))

                    if outpost_quantity > quantity:
                        outpost0["items"][item_id]["quantity"] -= quantity
                        item_copy["quantity"] = quantity
                        theater0["items"][item_id] = item_copy

                        apply_profile_changes.append({
                            "changeType": "itemAdded",
                            "itemId": item_id,
                            "item": item_copy
                        })

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": outpost0["items"][item_id]["quantity"]
                        })
                    else:
                        theater0["items"][item_id] = item_copy
                        del outpost0["items"][item_id]

                        apply_profile_changes.append({
                            "changeType": "itemAdded",
                            "itemId": item_id,
                            "item": item_copy
                        })

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemRemoved",
                            "itemId": item_id
                        })

            else:  
                if outpost_quantity != "Unknown" and theater_quantity != "Unknown":
                    if theater_quantity > quantity:
                        outpost0["items"][item_id]["quantity"] += quantity
                        theater0["items"][item_id]["quantity"] -= quantity

                        apply_profile_changes.append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": theater0["items"][item_id]["quantity"]
                        })

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": outpost0["items"][item_id]["quantity"]
                        })
                    else:
                        outpost0["items"][item_id]["quantity"] += theater_quantity
                        del theater0["items"][item_id]

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": outpost0["items"][item_id]["quantity"]
                        })

                        apply_profile_changes.append({
                            "changeType": "itemRemoved",
                            "itemId": item_id
                        })
                elif outpost_quantity == "Unknown" and theater_quantity != "Unknown":
                    item_copy = json.loads(json.dumps(theater0["items"][item_id]))

                    if theater_quantity > quantity:
                        theater0["items"][item_id]["quantity"] -= quantity
                        item_copy["quantity"] = quantity
                        outpost0["items"][item_id] = item_copy

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemAdded",
                            "itemId": item_id,
                            "item": item_copy
                        })

                        apply_profile_changes.append({
                            "changeType": "itemQuantityChanged",
                            "itemId": item_id,
                            "quantity": theater0["items"][item_id]["quantity"]
                        })
                    else:
                        outpost0["items"][item_id] = item_copy
                        del theater0["items"][item_id]

                        multi_update[0]["profileChanges"].append({
                            "changeType": "itemAdded",
                            "itemId": item_id,
                            "item": item_copy
                        })

                        apply_profile_changes.append({
                            "changeType": "itemRemoved",
                            "itemId": item_id
                        })

        stat_changed = True

    elif "theaterToOutpostItems" in body and "outpostToTheaterItems" in body:
        multi_update.append({
            "profileRevision": outpost0.get("rvn", 0),
            "profileId": "outpost0",
            "profileChangesBaseRevision": outpost0.get("rvn", 0),
            "profileChanges": [],
            "profileCommandRevision": outpost0.get("commandRevision", 0),
        })

        
        for item_transfer in body["theaterToOutpostItems"]:
            item_id = item_transfer["itemId"]
            quantity = int(item_transfer["quantity"])
            
            theater_quantity = get_item_quantity(theater0, item_id)
            outpost_quantity = get_item_quantity(outpost0, item_id)

            if outpost_quantity != "Unknown" and theater_quantity != "Unknown":
                if theater_quantity > quantity:
                    outpost0["items"][item_id]["quantity"] += quantity
                    theater0["items"][item_id]["quantity"] -= quantity

                    apply_profile_changes.append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": theater0["items"][item_id]["quantity"]
                    })

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": outpost0["items"][item_id]["quantity"]
                    })
                else:
                    outpost0["items"][item_id]["quantity"] += theater_quantity
                    del theater0["items"][item_id]

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": outpost0["items"][item_id]["quantity"]
                    })

                    apply_profile_changes.append({
                        "changeType": "itemRemoved",
                        "itemId": item_id
                    })
            elif outpost_quantity == "Unknown" and theater_quantity != "Unknown":
                item_copy = json.loads(json.dumps(theater0["items"][item_id]))

                if theater_quantity > quantity:
                    theater0["items"][item_id]["quantity"] -= quantity
                    item_copy["quantity"] = quantity
                    outpost0["items"][item_id] = item_copy

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": item_copy
                    })

                    apply_profile_changes.append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": theater0["items"][item_id]["quantity"]
                    })
                else:
                    outpost0["items"][item_id] = item_copy
                    del theater0["items"][item_id]

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": item_copy
                    })

                    apply_profile_changes.append({
                        "changeType": "itemRemoved",
                        "itemId": item_id
                    })

        
        for item_transfer in body["outpostToTheaterItems"]:
            item_id = item_transfer["itemId"]
            quantity = int(item_transfer["quantity"])
            
            theater_quantity = get_item_quantity(theater0, item_id)
            outpost_quantity = get_item_quantity(outpost0, item_id)

            if theater_quantity != "Unknown" and outpost_quantity != "Unknown":
                if outpost_quantity > quantity:
                    theater0["items"][item_id]["quantity"] += quantity
                    outpost0["items"][item_id]["quantity"] -= quantity

                    apply_profile_changes.append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": theater0["items"][item_id]["quantity"]
                    })

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": outpost0["items"][item_id]["quantity"]
                    })
                else:
                    theater0["items"][item_id]["quantity"] += outpost_quantity
                    del outpost0["items"][item_id]

                    apply_profile_changes.append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": theater0["items"][item_id]["quantity"]
                    })

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemRemoved",
                        "itemId": item_id
                    })
            elif theater_quantity == "Unknown" and outpost_quantity != "Unknown":
                item_copy = json.loads(json.dumps(outpost0["items"][item_id]))

                if outpost_quantity > quantity:
                    outpost0["items"][item_id]["quantity"] -= quantity
                    item_copy["quantity"] = quantity
                    theater0["items"][item_id] = item_copy

                    apply_profile_changes.append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": item_copy
                    })

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemQuantityChanged",
                        "itemId": item_id,
                        "quantity": outpost0["items"][item_id]["quantity"]
                    })
                else:
                    theater0["items"][item_id] = item_copy
                    del outpost0["items"][item_id]

                    apply_profile_changes.append({
                        "changeType": "itemAdded",
                        "itemId": item_id,
                        "item": item_copy
                    })

                    multi_update[0]["profileChanges"].append({
                        "changeType": "itemRemoved",
                        "itemId": item_id
                    })

        stat_changed = True

    if stat_changed:
        theater0["rvn"] = theater0.get("rvn", 0) + 1
        theater0["commandRevision"] = theater0.get("commandRevision", 0) + 1
        outpost0["rvn"] = outpost0.get("rvn", 0) + 1
        outpost0["commandRevision"] = outpost0.get("commandRevision", 0) + 1

        multi_update[0]["profileRevision"] = outpost0["rvn"]
        multi_update[0]["profileCommandRevision"] = outpost0["commandRevision"]

        with open(theater0_path, "w") as f:
            json.dump(theater0, f, indent=2)
        
        with open(outpost0_path, "w") as f:
            json.dump(outpost0, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": theater0
        }]

    return response.json({
        "profileRevision": theater0.get("rvn", 0),
        "profileId": "theater0",
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": theater0.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "multiUpdate": multi_update,
        "responseVersion": 1
    })

@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ModifyQuickbar")
async def modify_quickbar(request, path):
    profile_id = request.args.get("profileId", "theater0")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "primaryQuickbarChoices" in body:
        for i, item_id in enumerate(body["primaryQuickbarChoices"]):
            slot_number = i + 1
            if item_id == "":
                value = []
            else:
                value = [item_id.replace("-", "").upper()]
            
            profile["stats"]["attributes"]["player_loadout"]["primaryQuickBarRecord"]["slots"][str(slot_number)]["items"] = value
        
        stat_changed = True

    if "secondaryQuickbarChoice" in body and isinstance(body["secondaryQuickbarChoice"], str):
        if body["secondaryQuickbarChoice"] == "":
            value = []
        else:
            value = [body["secondaryQuickbarChoice"].replace("-", "").upper()]
        
        profile["stats"]["attributes"]["player_loadout"]["secondaryQuickBarRecord"]["slots"]["5"]["items"] = value
        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "statModified",
            "name": "player_loadout",
            "value": profile["stats"]["attributes"]["player_loadout"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/AssignHeroToLoadout")
async def assign_hero_to_loadout(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "loadoutId" in body and body["loadoutId"] in profile["items"] and "slotName" in body and "heroId" in body:
        loadout = profile["items"][body["loadoutId"]]
        crew_members = loadout["attributes"]["crew_members"]
        hero_id = body["heroId"]
        
        slot_name = body["slotName"]
        hero_id_lower = hero_id.lower()

        def clear_hero_from_slots(slots_to_clear):
            for slot in slots_to_clear:
                if crew_members.get(slot, "").lower() == hero_id_lower:
                    crew_members[slot] = ""

        if slot_name == "CommanderSlot":
            clear_hero_from_slots(["followerslot1", "followerslot2", "followerslot3", "followerslot4", "followerslot5"])
            crew_members["commanderslot"] = hero_id
            stat_changed = True

        elif slot_name == "FollowerSlot1":
            clear_hero_from_slots(["commanderslot", "followerslot2", "followerslot3", "followerslot4", "followerslot5"])
            crew_members["followerslot1"] = hero_id
            stat_changed = True

        elif slot_name == "FollowerSlot2":
            clear_hero_from_slots(["commanderslot", "followerslot1", "followerslot3", "followerslot4", "followerslot5"])
            crew_members["followerslot2"] = hero_id
            stat_changed = True

        elif slot_name == "FollowerSlot3":
            clear_hero_from_slots(["commanderslot", "followerslot1", "followerslot2", "followerslot4", "followerslot5"])
            crew_members["followerslot3"] = hero_id
            stat_changed = True

        elif slot_name == "FollowerSlot4":
            clear_hero_from_slots(["commanderslot", "followerslot1", "followerslot2", "followerslot3", "followerslot5"])
            crew_members["followerslot4"] = hero_id
            stat_changed = True

        elif slot_name == "FollowerSlot5":
            clear_hero_from_slots(["commanderslot", "followerslot1", "followerslot2", "followerslot3", "followerslot4"])
            crew_members["followerslot5"] = hero_id
            stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.append({
            "changeType": "itemAttrChanged",
            "itemId": body["loadoutId"],
            "attributeName": "crew_members",
            "attributeValue": profile["items"][body["loadoutId"]]["attributes"]["crew_members"]
        })

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })


@bp.post("/fortnite/api/game/v2/profile/<path:path>/client/ClearHeroLoadout")
async def clear_hero_loadout(request, path):
    profile_id = request.args.get("profileId", "campaign")
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_id}.json")

    with open(profile_path, "r") as f:
        profile = json.load(f)

    apply_profile_changes = []
    base_revision = profile.get("rvn", 0)
    query_revision = int(request.args.get("rvn", -1))
    stat_changed = False

    body = request.json or {}

    if "loadoutId" in body and body["loadoutId"] in profile["items"]:
        loadout = profile["items"][body["loadoutId"]]
        
        
        loadout["attributes"] = {
            "team_perk": "",
            "loadout_name": loadout["attributes"]["loadout_name"],
            "crew_members": {
                "followerslot5": "",
                "followerslot4": "",
                "followerslot3": "",
                "followerslot2": "",
                "followerslot1": "",
                "commanderslot": loadout["attributes"]["crew_members"]["commanderslot"]
            },
            "loadout_index": loadout["attributes"]["loadout_index"],
            "gadgets": [
                {
                    "gadget": "",
                    "slot_index": 0
                },
                {
                    "gadget": "",
                    "slot_index": 1
                }
            ]
        }

        stat_changed = True

    if stat_changed:
        profile["rvn"] = profile.get("rvn", 0) + 1
        profile["commandRevision"] = profile.get("commandRevision", 0) + 1

        apply_profile_changes.extend([
            {
                "changeType": "itemAttrChanged",
                "itemId": body["loadoutId"],
                "attributeName": "team_perk",
                "attributeValue": profile["items"][body["loadoutId"]]["attributes"]["team_perk"]
            },
            {
                "changeType": "itemAttrChanged",
                "itemId": body["loadoutId"],
                "attributeName": "crew_members",
                "attributeValue": profile["items"][body["loadoutId"]]["attributes"]["crew_members"]
            },
            {
                "changeType": "itemAttrChanged",
                "itemId": body["loadoutId"],
                "attributeName": "gadgets",
                "attributeValue": profile["items"][body["loadoutId"]]["attributes"]["gadgets"]
            }
        ])

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

    if query_revision != base_revision:
        apply_profile_changes = [{
            "changeType": "fullProfileUpdate",
            "profile": profile
        }]

    return response.json({
        "profileRevision": profile.get("rvn", 0),
        "profileId": profile_id,
        "profileChangesBaseRevision": base_revision,
        "profileChanges": apply_profile_changes,
        "profileCommandRevision": profile.get("commandRevision", 0),
        "serverTime": datetime.utcnow().isoformat() + "Z",
        "responseVersion": 1
    })

