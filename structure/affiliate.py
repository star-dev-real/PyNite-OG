from sanic import Sanic, json, NotFound
from sanic.router import Router
import json as json_module

with open("./responses/SAC.json", "r") as f:
    SupportedCodes = json_module.load(f)

def setup_routes(app: Sanic):
    
    @app.get("/affiliate/api/public/affiliates/slug/<slug:str>")
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
        
        # If no code found, return 404
        return json({}, status=404)
