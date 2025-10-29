import asyncio
import json
from .functions import MakeID, sleep

async def handle_matchmaker(ws):
    """Handle matchmaker WebSocket connection"""
    
    ticket_id = MakeID().replace("-", "")
    match_id = MakeID().replace("-", "")
    session_id = MakeID().replace("-", "")

    await connecting(ws)
    await sleep(800)
    await waiting(ws)
    await sleep(1000)
    await queued(ws, ticket_id)
    await sleep(4000)
    await session_assignment(ws, match_id)
    await sleep(2000)
    await join(ws, match_id, session_id)

async def connecting(ws):
    """Send Connecting status"""
    message = {
        "payload": {
            "state": "Connecting",
        },
        "name": "StatusUpdate",
    }
    await ws.send(json.dumps(message))

async def waiting(ws):
    """Send Waiting status"""
    message = {
        "payload": {
            "totalPlayers": 1,
            "connectedPlayers": 1,
            "state": "Waiting",
        },
        "name": "StatusUpdate",
    }
    await ws.send(json.dumps(message))

async def queued(ws, ticket_id):
    """Send Queued status"""
    message = {
        "payload": {
            "ticketId": ticket_id,
            "queuedPlayers": 0,
            "estimatedWaitSec": 0,
            "status": {},
            "state": "Queued",
        },
        "name": "StatusUpdate",
    }
    await ws.send(json.dumps(message))

async def session_assignment(ws, match_id):
    """Send SessionAssignment status"""
    message = {
        "payload": {
            "matchId": match_id,
            "state": "SessionAssignment",
        },
        "name": "StatusUpdate",
    }
    await ws.send(json.dumps(message))

async def join(ws, match_id, session_id):
    """Send Play command to join match"""
    message = {
        "payload": {
            "matchId": match_id,
            "sessionId": session_id,
            "joinDelaySec": 1,
        },
        "name": "Play",
    }
    await ws.send(json.dumps(message))