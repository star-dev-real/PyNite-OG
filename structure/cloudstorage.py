from sanic import Sanic, empty, raw, json
from sanic.response import ResponseStream
from sanic.handlers import ContentRangeHandler
import hashlib 
import os
import json as json_module
from pathlib import Path
from datetime import datetime
import urllib.parse
from .functions import GetVersionInfo

def setup_cloudstorage_routes(app: Sanic):
    @app.on_request
    async def extract_raw_body(request):
        if (request.path.lower().startswith("/fortnite/api/cloudstorage/user/") and request.method == "PUT"):
            request.raw_body = request.body

    @app.get("/fortnite/api/cloudstorage/system")
    async def get_cloudstorage_system(request):
        memory = GetVersionInfo()

        if 9.40 <= memory.build < 10.40:
            return empty(status=404)
        
        cloud_dir = Path(__file__).parent.parent / "CloudStorage"
        cloud_files = []

        for file_path in cloud_dir.glob("*.ini"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Calculate hashes
                    sha1_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()
                    sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                    cloud_files.append({
                        "uniqueFilename": file_path.name,
                        "filename": file_path.name,
                        "hash": sha1_hash,
                        "hash256": sha256_hash,
                        "length": len(content),
                        "contentType": "application/octet-stream",
                        "uploaded": datetime.utcnow().isoformat() + "Z",
                        "storageType": "S3",
                        "storageIds": {},
                        "doNotCache": True
                    })

            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

        return json(cloud_files)
    
    @app.get("/fortnite/api/cloudstorage/system/<file:str>")
    async def get_system_file(request, file: str):
        memory = GetVersionInfo(request)

        file_path = Path(__file__).parent.parent / "CloudStorage" / file

        if file_path.exists():
            with open(file_path, "rb") as f:
                content = f.read()

                if file == "DefaultEngine.ini" and getattr(memory, 'season', 0) >= 24:
                    content += b"\n[ConsoleVariables]\nnet.AllowEncyption=0\n"


                return raw(content, headers={"content_type": "application/octet-stream"})
        else:
            return empty(status=404)
        
    @app.get("/fortnite/api/cloudstorage/user/<account_id:path>/<file:str>")
    async def get_user_file(request, account_id: str, file: str):
        if os.getenv("LOCALAPPDATA"):
            client_settings_dir = Path(os.getenv("LOCALAPPDATA")) / "PyNiteOG" / "ClientSettings"
        else:
            client_settings_dir = Path(__file__).parent.parent / "ClientSettings"

        
        client_settings_dir.mkdir(parents=True, exist_ok=True)

        if file.lower() != "clientsettings.sav":
            return json({"error": "File not found"}, status=404)
        
        memory = GetVersionInfo(request)
        current_build_id = memory.CL

        if os.getenv("LOCALAPPDATA"):
            file_path = client_settings_dir / f"ClientSettings-{current_build_id}.Sav"
        else:
            file_path = client_settings_dir / f"ClientSettings-{current_build_id}.Sav"

        if file_path.exists():
            with open(file_path, "rb") as f:
                content = f.read()
            return raw(content, headers={"content_type": "application/octet-stream"})
        
        else:
            return empty(status=404)
        
    
    @app.get("/fortnite/api/cloudstorage/user/<account_id:str>")
    async def get_user_files(request, account_id: str):
        if os.getenv("LOCALAPPDATA"):
            client_settings_dir = Path(os.getenv("LOCALAPPDATA")) / "PyNiteOG" / "ClientSettings"
        else:
            client_settings_dir = Path(__file__).parent.parent / "ClientSettings"


        client_settings_dir.mkdir(parents=True, exist_ok=True)


        memory = GetVersionInfo(request)
        current_build_id = getattr(memory, 'CL', 'default')

        if os.getenv("LOCALAPPDATA"):
            file_path = client_settings_dir / f"ClientSettings-{current_build_id}.Sav"
        else:
            file_path = client_settings_dir / f"ClientSettings-{current_build_id}.Sav"

        if file_path.exists():
            with open(file_path, "rb") as f:
                content = f.read()

            file_stats = file_path.stat()

            # Calculate hashes
            sha1_hash = hashlib.sha1(content).hexdigest()
            sha256_hash = hashlib.sha256(content).hexdigest()

            return json([{
                "uniqueFilename": "ClientSettings.Sav",
                "filename": "ClientSettings.Sav",
                "hash": sha1_hash,
                "hash256": sha256_hash,
                "length": len(content.encode('latin1')),
                "contentType": "application/octet-stream",
                "uploaded": datetime.fromtimestamp(file_stats.st_mtime).isoformat() + 'Z',
                "storageType": "S3",
                "storageIds": {},
                "accountId": account_id,
                "doNotCache": True
            }])
        
        else:
            return json([])
        
    @app.put("/fortnite/api/cloudstorage/user/<account_id:path>/<file:str>")
    async def put_user_file(request, account_id: str, file: str):
        if os.getenv('LOCALAPPDATA'):
            client_settings_dir = Path(os.getenv('LOCALAPPDATA')) / "PyNiteOG" / "ClientSettings"
        else:
            client_settings_dir = Path(__file__).parent.parent / "ClientSettings"
        
        client_settings_dir.mkdir(parents=True, exist_ok=True)
        
        if file.lower() != "clientsettings.sav":
            return json({"error": "file not found"}, status=404)
        
        memory = GetVersionInfo(request)
        current_build_id = memory.CL
        
        if os.getenv('LOCALAPPDATA'):
            file_path = client_settings_dir / f"ClientSettings-{current_build_id}.Sav"
        else:
            file_path = client_settings_dir / f"ClientSettings-{current_build_id}.Sav"
        
        raw_body = getattr(request, 'raw_body', b'')
        with open(file_path, 'wb') as f:
            f.write(raw_body)
        
        return empty(status=204)