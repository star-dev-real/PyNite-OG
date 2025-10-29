from sanic import Blueprint, json
from sanic.response import empty, raw
import json as json_module
from pathlib import Path
import configparser
from datetime import datetime

bp = Blueprint("user", url_prefix="/")


CONFIG_PATH = Path(__file__).parent.parent / "Config" / "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)


Memory_CurrentAccountID = config.get("Config", "displayName", fallback="PyNiteOG")


SDK_PATH = Path(__file__).parent.parent / "responses" / "sdkv1.json"
with open(SDK_PATH, "r") as f:
    SDK_DATA = json_module.load(f)

@bp.get("/account/api/public/account")
async def get_accounts(request):
    response = []
    account_ids = request.args.get("accountId")
    
    if isinstance(account_ids, str):
        account_id = account_ids
        if "@" in account_id:
            account_id = account_id.split("@")[0]
        
        response.append({
            "id": account_id,
            "displayName": account_id,
            "externalAuths": {}
        })
    
    elif isinstance(account_ids, list):
        for account_id in account_ids:
            if "@" in account_id:
                account_id = account_id.split("@")[0]
            
            response.append({
                "id": account_id,
                "displayName": account_id,
                "externalAuths": {}
            })
    
    return json(response)

@bp.get("/account/api/public/account/<account_id:str>")
async def get_account(request, account_id):
    global Memory_CurrentAccountID
    
    if not config.getboolean("Config", "bUseConfigDisplayName", fallback=True):
        Memory_CurrentAccountID = account_id
    
    if "@" in Memory_CurrentAccountID:
        Memory_CurrentAccountID = Memory_CurrentAccountID.split("@")[0]
    
    return json({
        "id": account_id,
        "displayName": Memory_CurrentAccountID,
        "name": "PyNite",
        "email": f"{Memory_CurrentAccountID}@PyNite.com",
        "failedLoginAttempts": 0,
        "lastLogin": datetime.utcnow().isoformat() + "Z",
        "numberOfDisplayNameChanges": 0,
        "ageGroup": "UNKNOWN",
        "headless": False,
        "country": "US",
        "lastName": "Server",
        "preferredLanguage": "en",
        "canUpdateDisplayName": False,
        "tfaEnabled": False,
        "emailVerified": True,
        "minorVerified": False,
        "minorExpected": False,
        "minorStatus": "NOT_MINOR",
        "cabinedMode": False,
        "hasHashedEmail": False
    })

@bp.get("/sdk/v1/<path:path>")
async def get_sdk(request, path):
    return json(SDK_DATA)

@bp.post("/auth/v1/oauth/token")
async def post_auth_token(request):
    return json({
        "access_token": "PyNitestokenlol",
        "token_type": "bearer",
        "expires_in": 28800,
        "expires_at": "9999-12-31T23:59:59.999Z",
        "nonce": "PyNiteOG",
        "features": ["AntiCheat", "Connect", "Ecom", "Inventories", "LockerService"],
        "deployment_id": "PyNitesdeploymentidlol",
        "organization_id": "PyNitesorganizationidlol",
        "organization_user_id": "PyNitesorganisationuseridlol",
        "product_id": "prod-fn",
        "product_user_id": "PyNitesproductuseridlol",
        "product_user_id_created": False,
        "id_token": "PyNitesidtokenlol",
        "sandbox_id": "fn"
    })

@bp.get("/epic/id/v2/sdk/accounts")
async def get_sdk_accounts(request):
    return json([{
        "accountId": Memory_CurrentAccountID,
        "displayName": Memory_CurrentAccountID,
        "preferredLanguage": "en",
        "cabinedMode": False,
        "empty": False
    }])

@bp.post("/epic/oauth/v2/token")
async def post_epic_oauth_token(request):
    return json({
        "scope": "basic_profile friends_list openid presence",
        "token_type": "bearer",
        "access_token": "PyNitestokenlol",
        "expires_in": 28800,
        "expires_at": "9999-12-31T23:59:59.999Z",
        "refresh_token": "PyNitestokenlol",
        "refresh_expires_in": 86400,
        "refresh_expires_at": "9999-12-31T23:59:59.999Z",
        "account_id": Memory_CurrentAccountID,
        "client_id": "PyNitesclientidlol",
        "application_id": "PyNitesapplicationidlol",
        "selected_account_id": Memory_CurrentAccountID,
        "id_token": "PyNitestokenlol"
    })

@bp.get("/account/api/public/account/<path:path>/externalAuths")
async def get_external_auths(request, path):
    return json([])

@bp.delete("/account/api/oauth/sessions/kill")
async def delete_sessions(request):
    return empty(status=204)

@bp.delete("/account/api/oauth/sessions/kill/<path:path>")
async def delete_session(request, path):
    return empty(status=204)

@bp.get("/account/api/oauth/verify")
async def verify_oauth(request):
    return json({
        "token": "PyNitestokenlol",
        "session_id": "3c3662bcb661d6de679c636744c66b62",
        "token_type": "bearer",
        "client_id": "PyNitesclientidlol",
        "internal_client": True,
        "client_service": "fortnite",
        "account_id": Memory_CurrentAccountID,
        "expires_in": 28800,
        "expires_at": "9999-12-02T01:12:01.100Z",
        "auth_method": "exchange_code",
        "display_name": Memory_CurrentAccountID,
        "app": "fortnite",
        "in_app_id": Memory_CurrentAccountID,
        "device_id": "PyNitesdeviceidlol"
    })

@bp.post("/account/api/oauth/token")
async def post_account_oauth_token(request):
    global Memory_CurrentAccountID
    
    body = request.form if request.form else {}
    username = body.get("username", "PyNiteOG")
    
    if not config.getboolean("Config", "bUseConfigDisplayName", fallback=True):
        Memory_CurrentAccountID = username
    
    if "@" in Memory_CurrentAccountID:
        Memory_CurrentAccountID = Memory_CurrentAccountID.split("@")[0]
    
    return json({
        "access_token": "PyNitestokenlol",
        "expires_in": 28800,
        "expires_at": "9999-12-02T01:12:01.100Z",
        "token_type": "bearer",
        "refresh_token": "PyNitestokenlol",
        "refresh_expires": 86400,
        "refresh_expires_at": "9999-12-02T01:12:01.100Z",
        "account_id": Memory_CurrentAccountID,
        "client_id": "PyNitesclientidlol",
        "internal_client": True,
        "client_service": "fortnite",
        "displayName": Memory_CurrentAccountID,
        "app": "fortnite",
        "in_app_id": Memory_CurrentAccountID,
        "device_id": "PyNitesdeviceidlol"
    })

@bp.post("/account/api/oauth/exchange")
async def post_oauth_exchange(request):
    return json({})

@bp.get("/account/api/epicdomains/ssodomains")
async def get_sso_domains(request):
    return json([
        "unrealengine.com",
        "unrealtournament.com",
        "fortnite.com",
        "epicgames.com"
    ])

@bp.post("/fortnite/api/game/v2/tryPlayOnPlatform/account/<path:path>")
async def try_play_on_platform(request, path):
    return raw("true", content_type="text/plain")