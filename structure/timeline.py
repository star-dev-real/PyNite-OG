from sanic import Blueprint, json
from sanic.response import empty
import json as json_module
from pathlib import Path
import configparser
from datetime import datetime, timedelta
from .functions import GetVersionInfo

bp = Blueprint("timeline", url_prefix="/")

CONFIG_PATH = Path(__file__).parent.parent / "Config" / "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

@bp.get("/fortnite/api/calendar/v1/timeline")
async def get_timeline(request):
    memory = GetVersionInfo(request)
    
    active_events = [
        {
            "eventType": f"EventFlag.Season{memory['season']}",
            "activeUntil": "9999-01-01T00:00:00.000Z",
            "activeSince": "2020-01-01T00:00:00.000Z"
        },
        {
            "eventType": f"EventFlag.{memory['lobby']}",
            "activeUntil": "9999-01-01T00:00:00.000Z",
            "activeSince": "2020-01-01T00:00:00.000Z"
        }
    ]
    
    season = memory["season"]
    build = memory["build"]
    
    if season == 3:
        active_events.append({
            "eventType": "EventFlag.Spring2018Phase1",
            "activeUntil": "9999-01-01T00:00:00.000Z",
            "activeSince": "2020-01-01T00:00:00.000Z"
        })
        if build >= 3.1:
            active_events.append({
                "eventType": "EventFlag.Spring2018Phase2",
                "activeUntil": "9999-01-01T00:00:00.000Z",
                "activeSince": "2020-01-01T00:00:00.000Z"
            })

    elif season == 4:
        active_events.extend([
            {
                "eventType": "EventFlag.Blockbuster2018",
                "activeUntil": "9999-01-01T00:00:00.000Z",
                "activeSince": "2020-01-01T00:00:00.000Z"
            },
            {
                "eventType": "EventFlag.Blockbuster2018Phase1",
                "activeUntil": "9999-01-01T00:00:00.000Z",
                "activeSince": "2020-01-01T00:00:00.000Z"
            }
        ])

    if config.getboolean("Profile", "bAllSTWEventsActivated", fallback=False):
        stw_events = [
            "EventFlag.Blockbuster2018", "EventFlag.Blockbuster2018Phase1",
            "EventFlag.Blockbuster2018Phase2", "EventFlag.Blockbuster2018Phase3",
            "EventFlag.Blockbuster2018Phase4", "EventFlag.Fortnitemares"
        ]
        
        active_event_types = {event["eventType"] for event in active_events}
        for event_type in stw_events:
            if event_type not in active_event_types:
                active_events.append({
                    "eventType": event_type,
                    "activeUntil": "9999-01-01T00:00:00.000Z",
                    "activeSince": "2020-01-01T00:00:00.000Z"
                })
    
    state_template = {
        "activeStorefronts": [],
        "eventNamedWeights": {},
        "seasonNumber": memory["season"],
        "seasonTemplateId": f"AthenaSeason:athenaseason{memory['season']}",
        "matchXpBonusPoints": 0,
        "seasonBegin": "2020-01-01T13:00:00Z",
        "seasonEnd": "9999-01-01T14:00:00Z",
        "seasonDisplayedEnd": "9999-01-01T07:30:00Z",
        "weeklyStoreEnd": "9999-01-01T00:00:00Z",
        "stwEventStoreEnd": "9999-01-01T00:00:00.000Z",
        "stwWeeklyStoreEnd": "9999-01-01T00:00:00.000Z",
        "sectionStoreEnds": {
            "Featured": "9999-01-01T00:00:00.000Z"
        },
        "dailyStoreEnd": "9999-01-01T00:00:00Z"
    }
    
    states = [{
        "validFrom": "2020-01-01T00:00:00.000Z",
        "activeEvents": active_events.copy(),
        "state": state_template.copy()
    }]
    
    if build == 4.5 and config.getboolean("Events", "bEnableGeodeEvent", fallback=False):
        geode_start = config.get("Events", "geodeEventStartDate", fallback="2020-01-01T00:00:00.000Z")
        
        states[0]["activeEvents"].append({
            "eventType": "EventFlag.BR_S4_Geode_Countdown",
            "activeUntil": geode_start
        })
        
        states.append({
            "validFrom": geode_start,
            "activeEvents": active_events.copy(),
            "state": state_template.copy()
        })
        
        geode_end = (datetime.fromisoformat(geode_start.replace('Z', '+00:00')) + 
                    timedelta(minutes=3)).isoformat().replace('+00:00', 'Z')
        
        states[1]["activeEvents"].append({
            "eventType": "EventFlag.BR_S4_Geode_Begin",
            "activeUntil": geode_end
        })
        
        active_events.append({
            "eventType": "EventFlag.BR_S4_Geode_Over",
            "activeUntil": "9999-01-01T00:00:00.000Z"
        })
        
        states.append({
            "validFrom": geode_end,
            "activeEvents": active_events.copy(),
            "state": state_template.copy()
        })
    
    return json({
        "channels": {
            "client-matchmaking": {
                "states": [],
                "cacheExpire": "9999-01-01T22:28:47.830Z"
            },
            "client-events": {
                "states": states,
                "cacheExpire": "9999-01-01T22:28:47.830Z"
            }
        },
        "eventsTimeOffsetHrs": 0,
        "cacheIntervalMins": 10,
        "currentTime": datetime.utcnow().isoformat() + "Z"
    })