from sanic import Blueprint, json
import json as json_module

bp = Blueprint("affiliate")

with open("./responses/SAC.json", "r") as f:
    SupportedCodes = json_module.load(f)

@bp.get("/affiliate/api/public/affiliates/slug/<slug:str>")
async def get_affiliate_by_slug(request, slug: str):
    slug_lower = slug.lower()
    
    for code in SupportedCodes:
        if slug_lower == code.lower():
            return json({
                "id": code,
                "slug": code,
                "displayName": code,
                "status": "ACTIVE",
                "verified": False
            })
    
    return json({}, status=404)