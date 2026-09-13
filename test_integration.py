import os
﻿import json
from fastapi.testclient import TestClient
from app.main import app, get_db
from app.database import Base, engine, SessionLocal
from app import models

Base.metadata.create_all(bind=engine)
client = TestClient(app)
admin_key = os.environ.get("ADMIN_KEY", "")
H = {"X-Admin-Key": admin_key}

def test_integration_flow():
    # 1. Crear Link
    res = client.post("/api/links", headers=H, json={
        "slug": "test-telemetria-qa",
        "target_url": "https://www.canva.com/test",
        "name": "Test Telemetria",
        "category": "campaña"
    })
    
    # 2. Registrar Entregas 
    for _ in range(5):
        client.post("/api/links/test-telemetria-qa/deliver", headers=H, json={
            "channel": "whatsapp"
        })

    # 3. Registrar Clics
    client.get("/test-telemetria-qa", headers={"X-Forwarded-For": "10.0.0.1"})
    client.get("/test-telemetria-qa", headers={"X-Forwarded-For": "10.0.0.2"})
    client.get("/test-telemetria-qa", headers={"X-Forwarded-For": "10.0.0.2"})

    # 4. Validar Stats
    res_links = client.get("/api/links", headers=H)
    try:
        link_id = next(l["id"] for l in res_links.json() if l["slug"] == "test-telemetria-qa")
        res_stats = client.get("/api/links/{link_id}/stats", headers=H)
        stats = res_stats.json()
        print("--- RESULTADO QA CTR ---")
        print(f"Clics Unicos: {stats.get('unique_clicks', 0)} / Entregados: {stats.get('deliveries_count', 0)}")
        print(f"CTR: {stats.get('ctr', 0)}%")
        client.delete("/api/links/{link_id}", headers=H)
    except Exception as e:
        print("Error en QA:", e)

if __name__ == "__main__":
    test_integration_flow()
