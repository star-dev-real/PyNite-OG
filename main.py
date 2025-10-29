from sanic import Sanic, json
from sanic.response import empty
import os
from pathlib import Path
import asyncio

try:
    from structure.party import bp as party_bp
    from structure.discovery import bp as discovery_bp
    from structure.privacy import bp as privacy_bp
    from structure.timeline import bp as timeline_bp
    from structure.user import bp as user_bp
    from structure.contentpages import bp as contentpages_bp
    from structure.friends import bp as friends_bp
    from structure.main import bp as main_bp
    from structure.storefront import bp as storefront_bp
    from structure.version import bp as version_bp
    from structure.lightswitch import bp as lightswitch_bp
    from structure.affiliate import bp as affiliate_bp
    from structure.matchmaking import bp as matchmaking_bp
    from structure.cloudstorage import bp as cloudstorage_bp
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all structure modules have 'bp' blueprint defined")
    exit(1)

app = Sanic("PyNiteOG")

app.config.FALLBACK_ERROR_FORMAT = "json"

blueprints = [
    (party_bp, "party"),
    (discovery_bp, "discovery"),
    (privacy_bp, "privacy"),
    (timeline_bp, "timeline"),
    (user_bp, "user"),
    (contentpages_bp, "contentpages"),
    (friends_bp, "friends"),
    (main_bp, "main"),
    (storefront_bp, "storefront"),
    (version_bp, "version"),
    (lightswitch_bp, "lightswitch"),
    (affiliate_bp, "affiliate"),
    (matchmaking_bp, "matchmaking"),
    (cloudstorage_bp, "cloudstorage"),
]

for bp, name in blueprints:
    try:
        app.blueprint(bp)
        print(f"✅ Registered blueprint: {name}")
    except Exception as e:
        print(f"❌ Failed to register blueprint {name}: {e}")

@app.route("/")
async def root(request):
    return json({"status": "PyNiteOG is running"})

@app.route("/health")
async def health_check(request):
    return json({"status": "healthy"})

@app.exception(404)
async def handle_404(request, exception):
    return json({
        "errorCode": "errors.com.PyNiteOG.common.not_found",
        "errorMessage": "Sorry the resource you were trying to find could not be found",
        "numericErrorCode": 1004,
        "originatingService": "any",
        "intent": "prod"
    }, status=404, headers={
        'X-Epic-Error-Name': 'errors.com.PyNiteOG.common.not_found',
        'X-Epic-Error-Code': '1004'
    })

@app.exception(Exception)
async def handle_exception(request, exception):
    print(f"Global exception handler: {exception}")
    return json({
        "errorCode": "errors.com.PyNiteOG.common.internal_error",
        "errorMessage": "Internal server error",
        "numericErrorCode": 1000,
        "originatingService": "any",
        "intent": "prod"
    }, status=500)

async def setup_directories():
    try:
        local_app_data = os.getenv('LOCALAPPDATA')
        if local_app_data:
            PyNite_server_dir = Path(local_app_data) / "PyNiteOG"
            PyNite_server_dir.mkdir(exist_ok=True)
            print(f"Created directory: {PyNite_server_dir}")
        else:
            client_settings_dir = Path(__file__).parent / "ClientSettings"
            client_settings_dir.mkdir(exist_ok=True)
            print(f"Created directory: {client_settings_dir}")
    except Exception as e:
        print(f"Error creating directories: {e}")

if __name__ == "__main__":
    asyncio.run(setup_directories())
    
    port = int(os.getenv('PORT', 3551))
    
    async def start_servers():
        from structure.xmpp import start_xmpp_server
        await start_xmpp_server(80)
        
        print(f"PyNiteOG started listening on port {port}")
        
        await app.run(host="0.0.0.0", port=port, debug=False, access_log=True)
    
    try:
        asyncio.run(start_servers())
    except OSError as e:
        if e.errno == 48 or "Address already in use" in str(e):
            print(f"\033[31mERROR\033[0m: Port {port} is already in use!")
        else:
            raise e
    except KeyboardInterrupt:
        print("\nShutting down PyNiteOG...")
    except Exception as e:
        print(f"Unexpected error: {e}")