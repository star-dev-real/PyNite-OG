from sanic import Blueprint, json
from datetime import datetime

bp = Blueprint("version", url_prefix="/")

@bp.get("/fortnite/api/version")
async def get_version(request):
    return json({
        "app": "fortnite",
        "serverDate": datetime.utcnow().isoformat() + "Z",
        "overridePropertiesVersion": "unknown",
        "cln": "17951730",
        "build": "444",
        "moduleName": "Fortnite-Core",
        "buildDate": "2021-10-27T21:00:51.697Z",
        "version": "18.30",
        "branch": "Release-18.30",
        "modules": {
            "Epic-LightSwitch-AccessControlCore": {
                "cln": "17237679",
                "build": "b2130",
                "buildDate": "2021-08-19T18:56:08.144Z",
                "version": "1.0.0",
                "branch": "trunk"
            },
            "epic-xmpp-api-v1-base": {
                "cln": "5131a23c1470acbd9c94fae695ef7d899c1a41d6",
                "build": "b3595",
                "buildDate": "2019-07-30T09:11:06.587Z",
                "version": "0.0.1",
                "branch": "master"
            },
            "epic-common-core": {
                "cln": "17909521",
                "build": "3217",
                "buildDate": "2021-10-25T18:41:12.486Z",
                "version": "3.0",
                "branch": "TRUNK"
            }
        }
    })

@bp.get("/fortnite/api/v2/versioncheck/<path:path>")
async def version_check_v2_path(request, path):
    return json({
        "type": "NO_UPDATE"
    })

@bp.get("/fortnite/api/v2/versioncheck<path:path>")
async def version_check_v2(request, path):
    return json({
        "type": "NO_UPDATE"
    })

@bp.get("/fortnite/api/versioncheck<path:path>")
async def version_check(request, path):
    return json({
        "type": "NO_UPDATE"
    })