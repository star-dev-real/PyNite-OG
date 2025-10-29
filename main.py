# main.py
from sanic import Sanic, json
from sanic.response import empty
import os
from pathlib import Path
import asyncio

# Import route modules with proper relative imports
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
# from structure.mcp import bp as mcp_bp

app = Sanic("PyNiteOG")

# Configure app
app.config.FALLBACK_ERROR_FORMAT = "json"

app.blueprint(party_bp)
app.blueprint(discovery_bp)
app.blueprint(privacy_bp)
app.blueprint(timeline_bp)
app.blueprint(user_bp)
app.blueprint(contentpages_bp)
app.blueprint(friends_bp)
app.blueprint(main_bp)
app.blueprint(storefront_bp)
app.blueprint(version_bp)
app.blueprint(lightswitch_bp)
app.blueprint(affiliate_bp)
app.blueprint(matchmaking_bp)
app.blueprint(cloudstorage_bp)
# app.blueprint(mcp_bp)

@app.route("/")
async def root(request):
    return json({"status": "PyNiteOG is running"})

# 404 handler
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

async def setup_directories():
    """Create necessary directories"""
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
        await app.create_server(host="0.0.0.0", port=port)
        
        await asyncio.Future()
    
    try:
        asyncio.run(start_servers())
    except OSError as e:
        if e.errno == 48 or "Address already in use" in str(e):
            print(f"\033[31mERROR\033[0m: Port {port} is already in use!")
        else:
            raise e