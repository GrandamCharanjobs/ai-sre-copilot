from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json

app = FastAPI(title="AI SRE Co-Pilot", version="1.0.0")
templates = Jinja2Templates(directory="templates")

class Alert(BaseModel):
    alert_id: str
    severity: str
    message: str
    service: str
    timestamp: str = None

def init_db():
    conn = sqlite3.connect('incidents.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts 
                 (id TEXT PRIMARY KEY, severity TEXT, message TEXT, service TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS incidents 
                 (id TEXT PRIMARY KEY, severity TEXT, summary TEXT, alerts_count INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def dashboard(request: Request):
    conn = sqlite3.connect('incidents.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM alerts")
    alert_count = c.fetchone()[0]
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 5")
    recent_alerts = [{"id": row[0], "severity": row[1], "message": row[2], "service": row[3]} for row in c.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "alert_count": alert_count,
        "recent_alerts": recent_alerts
    })

@app.post("/ingest/alert")
async def ingest_alert(alert: Alert):
    timestamp = alert.timestamp or datetime.now().isoformat()
    conn = sqlite3.connect('incidents.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO alerts VALUES (?, ?, ?, ?, ?)",
              (alert.alert_id, alert.severity, alert.message, alert.service, timestamp))
    conn.commit()
    conn.close()
    return {"status": "ingested", "alert_id": alert.alert_id, "timestamp": timestamp}

@app.get("/api/alerts")
async def get_alerts():
    conn = sqlite3.connect('incidents.db')
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10")
    alerts = [{"id": row[0], "severity": row[1], "message": row[2], "service": row[3], "timestamp": row[4]} for row in c.fetchall()]
    conn.close()
    return {"alerts": alerts, "count": len(alerts)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
