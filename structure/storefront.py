from sanic import Blueprint, json
from sanic.response import empty
import json as json_module
from pathlib import Path
from .functions import getItemShop, GetVersionInfo

bp = Blueprint("storefront", url_prefix="/")


KEYCHAIN_PATH = Path(__file__).parent.parent / "responses" / "keychain.json"
with open(KEYCHAIN_PATH, "r") as f:
    KEYCHAIN_DATA = json_module.load(f)

@bp.get("/fortnite/api/storefront/v2/catalog")
async def get_catalog(request):
    user_agent = request.headers.get("user-agent", "")
    
    
    if "2870186" in user_agent:
        return empty(status=404)
    
    catalog = getItemShop()
    memory = GetVersionInfo(request)
    
    
    catalog_str = json_module.dumps(catalog)
    
    if memory["build"] >= 30.10:
        catalog_str = catalog_str.replace('"Normal"', '"Size_1_x_2"')
    
    if memory["build"] >= 30.20:
        catalog_str = catalog_str.replace('Game/Items/CardPacks/', 'SaveTheWorld/Items/CardPacks/')
    
    
    if memory["build"] >= 30.10 or memory["build"] >= 30.20:
        catalog = json_module.loads(catalog_str)
    
    return json(catalog)

@bp.get("/fortnite/api/storefront/v2/keychain")
async def get_keychain(request):
    return json(KEYCHAIN_DATA)

@bp.get("/catalog/api/shared/bulk/offers")
async def get_bulk_offers(request):
    return json({})