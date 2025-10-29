import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
import websockets
from websockets.server import WebSocketServerProtocol
import xml.etree.ElementTree as ET
import xml.dom.minidom
from structure import functions

class XMPPServer:
    def __init__(self, port: int = 80):
        self.port = port
        self.clients: List[Dict] = []
        self.server = None
    
    async def start(self):
        try:
            self.server = await websockets.serve(
                self.handle_connection,
                "0.0.0.0",
                self.port,
                subprotocols=["xmpp"]
            )
            print(f"XMPP and Matchmaker started listening on port {self.port}")
        except Exception as e:
            print(f"XMPP and Matchmaker \033[31mFAILED\033[0m to start hosting: {e}")
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        try:
            if websocket.subprotocol and websocket.subprotocol.lower() == "xmpp":
                await self.handle_xmpp_client(websocket)
            else:
                await self.handle_matchmaker(websocket)
        except Exception as e:
            print(f"Connection error: {e}")
    
    async def handle_xmpp_client(self, ws: WebSocketServerProtocol):
        account_id = ""
        jid = ""
        client_id = ""
        connection_id = functions.MakeID()
        authenticated = False
        client_data = None
        
        try:
            async for message in ws:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                
                try:
                    root = ET.fromstring(message)
                except ET.ParseError:
                    await self.send_error(ws)
                    continue
                
                tag = root.tag
                
                if tag == "open":
                    await self.send_open_response(ws, connection_id, authenticated)
                
                elif tag == "auth":
                    if not root.text or not await self.authenticate_client(root.text, ws):
                        await self.send_error(ws)
                        continue
                    
                    decoded = functions.DecodeBase64(root.text)
                    parts = decoded.split('\x00')
                    if len(parts) == 3:
                        account_id = parts[1]
                        authenticated = True
                        print(f"An xmpp client with the account id {account_id} has logged in.")
                        await self.send_success(ws)
                
                elif tag == "iq":
                    await self.handle_iq(root, ws, account_id, jid, client_id, connection_id)
                
                elif tag == "message":
                    await self.handle_message(root, ws, jid)
                
                elif tag == "presence":
                    await self.handle_presence(root, ws, jid)
                
                if authenticated and account_id and jid and not client_data:
                    if not any(client['ws'] == ws for client in self.clients):
                        client_data = {
                            "ws": ws,
                            "accountId": account_id,
                            "jid": jid,
                            "id": client_id,
                            "lastPresenceUpdate": {
                                "away": False,
                                "status": "{}"
                            }
                        }
                        self.clients.append(client_data)
                        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.remove_client(ws)
    
    async def handle_matchmaker(self, ws: WebSocketServerProtocol):
        try:
            async for message in ws:
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def send_open_response(self, ws: WebSocketServerProtocol, connection_id: str, authenticated: bool):
        if authenticated:
            response = self.create_xml_element("stream:features", {
                "xmlns:stream": "http://etherx.jabber.org/streams"
            })
            response.append(self.create_xml_element("ver", {"xmlns": "urn:xmpp:features:rosterver"}))
            response.append(self.create_xml_element("starttls", {"xmlns": "urn:ietf:params:xml:ns:xmpp-tls"}))
            response.append(self.create_xml_element("bind", {"xmlns": "urn:ietf:params:xml:ns:xmpp-bind"}))
            
            compression = self.create_xml_element("compression", {"xmlns": "http://jabber.org/features/compress"})
            compression.append(self.create_xml_element("method", text="zlib"))
            response.append(compression)
            
            response.append(self.create_xml_element("session", {"xmlns": "urn:ietf:params:xml:ns:xmpp-session"}))
        else:
            response = self.create_xml_element("stream:features", {
                "xmlns:stream": "http://etherx.jabber.org/streams"
            })
            
            mechanisms = self.create_xml_element("mechanisms", {"xmlns": "urn:ietf:params:xml:ns:xmpp-sasl"})
            mechanisms.append(self.create_xml_element("mechanism", text="PLAIN"))
            response.append(mechanisms)
            
            response.append(self.create_xml_element("ver", {"xmlns": "urn:xmpp:features:rosterver"}))
            response.append(self.create_xml_element("starttls", {"xmlns": "urn:ietf:params:xml:ns:xmpp-tls"}))
            
            compression = self.create_xml_element("compression", {"xmlns": "http://jabber.org/features/compress"})
            compression.append(self.create_xml_element("method", text="zlib"))
            response.append(compression)
            
            response.append(self.create_xml_element("auth", {"xmlns": "http://jabber.org/features/iq-auth"}))
        
        open_response = self.create_xml_element("open", {
            "xmlns": "urn:ietf:params:xml:ns:xmpp-framing",
            "from": "prod.ol.epicgames.com",
            "id": connection_id,
            "version": "1.0",
            "xml:lang": "en"
        })
        
        await ws.send(self.xml_to_string(open_response))
        await ws.send(self.xml_to_string(response))
    
    async def authenticate_client(self, auth_data: str, ws: WebSocketServerProtocol) -> bool:
        try:
            if not auth_data:
                return False
            
            decoded = functions.DecodeBase64(auth_data)
            if not decoded or '\x00' not in decoded:
                return False
            
            parts = decoded.split('\x00')
            if len(parts) != 3:
                return False
            
            account_id = parts[1]
            if any(client['accountId'] == account_id for client in self.clients):
                return False
            
            return True
        except Exception:
            return False
    
    async def send_success(self, ws: WebSocketServerProtocol):
        success = self.create_xml_element("success", {
            "xmlns": "urn:ietf:params:xml:ns:xmpp-sasl"
        })
        await ws.send(self.xml_to_string(success))
    
    async def handle_iq(self, root: ET.Element, ws: WebSocketServerProtocol, account_id: str, jid: str, client_id: str, connection_id: str):
        iq_id = root.get('id')
        
        if iq_id == "_xmpp_bind1":
            bind_elem = root.find(".//bind")
            if bind_elem is not None:
                resource_elem = bind_elem.find("resource")
                if resource_elem is not None and resource_elem.text:
                    resource = resource_elem.text
                    jid = f"{account_id}@prod.ol.epicgames.com/{resource}"
                    client_id = f"{account_id}@prod.ol.epicgames.com"
                    
                    response = self.create_xml_element("iq", {
                        "to": jid,
                        "id": "_xmpp_bind1",
                        "xmlns": "jabber:client",
                        "type": "result"
                    })
                    
                    bind = self.create_xml_element("bind", {
                        "xmlns": "urn:ietf:params:xml:ns:xmpp-bind"
                    })
                    bind.append(self.create_xml_element("jid", text=jid))
                    response.append(bind)
                    
                    await ws.send(self.xml_to_string(response))
        
        elif iq_id == "_xmpp_session1":
            if not any(client['ws'] == ws for client in self.clients):
                await self.send_error(ws)
                return
            
            response = self.create_xml_element("iq", {
                "to": jid,
                "from": "prod.ol.epicgames.com",
                "id": "_xmpp_session1",
                "xmlns": "jabber:client",
                "type": "result"
            })
            await ws.send(self.xml_to_string(response))
            await self.get_presence_from_all(ws)
        
        else:
            if not any(client['ws'] == ws for client in self.clients):
                await self.send_error(ws)
                return
            
            response = self.create_xml_element("iq", {
                "to": jid,
                "from": "prod.ol.epicgames.com",
                "id": iq_id,
                "xmlns": "jabber:client",
                "type": "result"
            })
            await ws.send(self.xml_to_string(response))
    
    async def handle_message(self, root: ET.Element, ws: WebSocketServerProtocol, jid: str):
        if not any(client['ws'] == ws for client in self.clients):
            await self.send_error(ws)
            return
        
        body_elem = root.find("body")
        if body_elem is None or not body_elem.text:
            return
        
        body = body_elem.text
        msg_type = root.get('type')
        
        if msg_type == "chat":
            to_jid = root.get('to')
            if not to_jid:
                return
            
            sender = next((client for client in self.clients if client['ws'] == ws), None)
            receiver = next((client for client in self.clients if client['id'] == to_jid), None)
            
            if not receiver or not sender or receiver == sender:
                return
            
            message = self.create_xml_element("message", {
                "to": receiver['jid'],
                "from": sender['jid'],
                "xmlns": "jabber:client",
                "type": "chat"
            })
            message.append(self.create_xml_element("body", text=body))
            
            await receiver['ws'].send(self.xml_to_string(message))
            return
        
        if self.is_json(body):
            try:
                obj = json.loads(body)
                if 'type' in obj and isinstance(obj['type'], str):
                    if obj['type'].lower() == "com.epicgames.party.invitation":
                        to_jid = root.get('to')
                        if not to_jid:
                            return
                        
                        sender = next((client for client in self.clients if client['ws'] == ws), None)
                        receiver = next((client for client in self.clients if client['id'] == to_jid), None)
                        
                        if not receiver:
                            return
                        
                        message = self.create_xml_element("message", {
                            "from": sender['jid'],
                            "id": root.get('id', ''),
                            "to": receiver['jid'],
                            "xmlns": "jabber:client"
                        })
                        message.append(self.create_xml_element("body", text=body))
                        
                        await receiver['ws'].send(self.xml_to_string(message))
                    else:
                        message = self.create_xml_element("message", {
                            "from": jid,
                            "id": root.get('id', ''),
                            "to": jid,
                            "xmlns": "jabber:client"
                        })
                        message.append(self.create_xml_element("body", text=body))
                        await ws.send(self.xml_to_string(message))
            except json.JSONDecodeError:
                pass
    
    async def handle_presence(self, root: ET.Element, ws: WebSocketServerProtocol, jid: str):
        if not any(client['ws'] == ws for client in self.clients):
            await self.send_error(ws)
            return
        
        status_elem = root.find("status")
        if status_elem is None or not status_elem.text or not self.is_json(status_elem.text):
            return
        
        body = status_elem.text
        show_elem = root.find("show")
        away = show_elem is not None
        
        await self.update_presence_for_all(ws, body, away, False)
    
    async def update_presence_for_all(self, ws: WebSocketServerProtocol, body: str, away: bool, offline: bool):
        sender_data = next((client for client in self.clients if client['ws'] == ws), None)
        if not sender_data:
            await self.send_error(ws)
            return
        
        sender_index = self.clients.index(sender_data)
        self.clients[sender_index]['lastPresenceUpdate']['away'] = away
        self.clients[sender_index]['lastPresenceUpdate']['status'] = body
        
        for client_data in self.clients:
            presence = self.create_xml_element("presence", {
                "to": client_data['jid'],
                "xmlns": "jabber:client",
                "from": sender_data['jid']
            })
            
            if offline:
                presence.set("type", "unavailable")
            else:
                presence.set("type", "available")
            
            if away and not offline:
                presence.append(self.create_xml_element("show", text="away"))
            
            if not offline:
                presence.append(self.create_xml_element("status", text=body))
            
            await client_data['ws'].send(self.xml_to_string(presence))
    
    async def get_presence_from_all(self, ws: WebSocketServerProtocol):
        sender_data = next((client for client in self.clients if client['ws'] == ws), None)
        if not sender_data:
            await self.send_error(ws)
            return
        
        for client_data in self.clients:
            presence = self.create_xml_element("presence", {
                "to": sender_data['jid'],
                "xmlns": "jabber:client",
                "from": client_data['jid'],
                "type": "available"
            })
            
            if client_data['lastPresenceUpdate']['away']:
                presence.append(self.create_xml_element("show", text="away"))
            
            presence.append(self.create_xml_element("status", text=client_data['lastPresenceUpdate']['status']))
            
            await sender_data['ws'].send(self.xml_to_string(presence))
    
    async def remove_client(self, ws: WebSocketServerProtocol):
        client_data = next((client for client in self.clients if client['ws'] == ws), None)
        if client_data:
            await self.update_presence_for_all(ws, "{}", False, True)
            print(f"An xmpp client with the account id {client_data['accountId']} has logged out.")
            self.clients.remove(client_data)
    
    async def send_error(self, ws: WebSocketServerProtocol):
        try:
            close_elem = self.create_xml_element("close", {
                "xmlns": "urn:ietf:params:xml:ns:xmpp-framing"
            })
            await ws.send(self.xml_to_string(close_elem))
            await ws.close()
        except:
            pass
    
    def create_xml_element(self, tag: str, attrs: Dict[str, str] = None, text: str = None) -> ET.Element:
        element = ET.Element(tag)
        if attrs:
            for key, value in attrs.items():
                element.set(key, value)
        if text:
            element.text = text
        return element
    
    def xml_to_string(self, element: ET.Element) -> str:
        return ET.tostring(element, encoding='unicode', short_empty_elements=False)
    
    def is_json(self, text: str) -> bool:
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

xmpp_server = XMPPServer()

async def start_xmpp_server(port: int = 80):
    global xmpp_server
    xmpp_server = XMPPServer(port)
    await xmpp_server.start()

async def sendXmppMessageToAll(body):
    if isinstance(body, dict):
        body = json.dumps(body)
    
    for client in xmpp_server.clients:
        try:
            message = xmpp_server.create_xml_element("message", {
                "from": "xmpp-admin@prod.ol.epicgames.com",
                "xmlns": "jabber:client",
                "to": client['jid']
            })
            message.append(xmpp_server.create_xml_element("body", text=body))
            await client['ws'].send(xmpp_server.xml_to_string(message))
        except Exception as e:
            print(f"Error sending XMPP message: {e}")