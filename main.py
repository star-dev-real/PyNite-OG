from sanic import Sanic, json, text
from sanic.response import empty
from sanic.exceptions import NotFound
import os
from pathlib import Path
import asyncio


from structure import party, discovery, privacy, timeline, user, contentpages
from structure import friends, main, storefront, version, lightswitch, affiliate
from structure import matchmaking, cloudstorage, mcp
from structure.xmpp import start_xmpp_server

def create_app():
    app = Sanic("PyNiteOG")
    
    
    app.config.FALLBACK_ERROR_FORMAT = "json"
    
    
    app.static('/public', './public')
    
    
    app.blueprint(party.bp)
    app.blueprint(discovery.bp)
    app.blueprint(privacy.bp)
    app.blueprint(timeline.bp)
    app.blueprint(user.bp)
    app.blueprint(contentpages.bp)
    app.blueprint(friends.bp)
    app.blueprint(main.bp)
    app.blueprint(storefront.bp)
    app.blueprint(version.bp)
    app.blueprint(lightswitch.bp)
    app.blueprint(affiliate.bp)
    app.blueprint(matchmaking.bp)
    app.blueprint(cloudstorage.bp)
    app.blueprint(mcp.bp)
    
    
    @app.exception(NotFound)
    async def handle_404(request, exception):
        x_epic_error_name = "errors.com.PyNiteOG.common.not_found"
        x_epic_error_code = 1004
        
        return json({
            "errorCode": x_epic_error_name,
            "errorMessage": "Sorry the resource you were trying to find could not be found",
            "numericErrorCode": x_epic_error_code,
            "originatingService": "any",
            "intent": "prod"
        }, status=404, headers={
            'X-Epic-Error-Name': x_epic_error_name,
            'X-Epic-Error-Code': str(x_epic_error_code)
        })
    
    return app

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

async def main():
    
    await setup_directories()
    
    
    app = create_app()
    
    
    port = int(os.getenv('PORT', 3551))
    
    try:
        
        print("Starting XMPP server...")
        await start_xmpp_server(80)  
        
        
        print(f"PyNiteOG started listening on port {port}")
        await app.create_server(
            host="0.0.0.0",
            port=port,
            return_asyncio_server=True
        )
        
        
        await asyncio.Future()  
        
    except OSError as e:
        if e.errno == 48 or "Address already in use" in str(e):
            print(f"\033[31mERROR\033[0m: Port {port} is already in use!")
        else:
            raise e
        return 1
    except Exception as e:
        print(f"Failed to start server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)