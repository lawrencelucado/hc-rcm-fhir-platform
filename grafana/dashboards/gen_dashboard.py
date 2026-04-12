import json

DS = "rcm-postgres"

def pg():
    return {"type": "grafana-postgresql-datasource", "uid": DS}

def stat_panel(pid, title, sql, unit="short", x=0, y=0, w=6, h=4):
    return {
        "id": pid, "type": "stat", "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": pg(),
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"]},
            "colorMode": "background", "graphMode": "none", "textMode": "auto"
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
            },
            "overrides": []
        },
        "targets": [{"datasource": pg(), "format": "table", "rawQuery": True, "rawSql": sql, "refId": "A"}]
    }

def table_panel(pid, title, sql, x=0, y=0, w=24, h=8):
    return {
        "id": pid, "type": "table", "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": pg(),
        "options": {"sortBy": []},
        "fieldConfig": {
            "defaults": {},
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "denial_rate_pct"},
                    "properties": [
                        {"id": "custom.displayMode", "value": "color-background"},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 20},
                            {"color": "orange", "value": 35},
                            {"color": "red", "value": 50}
                        ]}}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "payer_grade"},
                    "properties": [
                        {"id": "custom.displayMode", "value": "color-background"},
                        {"id": "mappings", "value": [
                            {"type": "value", "options": {
                                "A": {"color": "green", "text": "A", "index": 0},
                                "B": {"color": "blue", "text": "B", "index": 1},
                                "C": {"color": "yellow", "text": "C", "index": 2},
                                "D": {"color": "red", "text": "D", "index": 3}
                            }}
                        ]}
                    ]
                }
            ]
        },
        "targets": [{"datasource": pg(), "format": "table", "rawQuery": True, "rawSql": sql, "refId": "A"}]
    }

def bar_panel(pid, title, sql, unit="short", x=0, y=0, w=12, h=8, stacking="none", orientation="horizontal"):
    return {
        "id": pid, "type": "barchart", "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": pg(),
        "options": {"xField": "payer_name", "barWidth": 0.7, "orientation": orientation, "stacking": stacking},
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "targets": [{"datasource": pg(), "format": "table", "rawQuery": True, "rawSql": sql, "refId": "A"}]
    }

def pie_panel(pid, title, sql, x=0, y=0, w=12, h=8):
    return {
        "id": pid, "type": "piechart", "title": title,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": pg(),
        "options": {"pieType": "donut", "legendDisplayMode": "table", "legendPlacement": "right"},
        "fieldConfig": {"defaults": {}, "overrides": []},
        "targets": [{"datasource": pg(), "format": "table", "rawQuery": True, "rawSql": sql, "refId": "A"}]
    }

panels = [
    stat_panel(1, "Total Claims", "SELECT COUNT(*) AS value FROM raw.claims", x=0, y=0, w=6, h=4),
    stat_panel(2, "Total Billed", "SELECT SUM(total_billed)::bigint AS value FROM curated_mart.payer_scorecard", unit="currencyUSD", x=6, y=0, w=6, h=4),
    stat_panel(3, "Total Paid", "SELECT SUM(total_paid)::bigint AS value FROM curated_mart.payer_scorecard", unit="currencyUSD", x=12, y=0, w=6, h=4),
    stat_panel(4, "Total Denied", "SELECT SUM(total_denied)::bigint AS value FROM curated_mart.payer_scorecard", unit="currencyUSD", x=18, y=0, w=6, h=4),
    bar_panel(
        5, "Denial Rate by Payer (%)",
        "SELECT payer_name, denial_rate_pct FROM curated_mart.payer_scorecard ORDER BY denial_rate_pct DESC",
        unit="percent", x=0, y=4, w=12, h=8
    ),
    pie_panel(
        6, "Top Denial Codes",
        "SELECT denial_code, SUM(denial_count) AS count FROM curated_mart.denial_summary GROUP BY denial_code ORDER BY count DESC LIMIT 10",
        x=12, y=4, w=12, h=8
    ),
    table_panel(
        7, "Payer Scorecard",
        "SELECT payer_name, payer_type, total_claims, ROUND(total_billed::numeric,2) AS total_billed, ROUND(total_paid::numeric,2) AS total_paid, ROUND(denial_rate_pct::numeric,1) AS denial_rate_pct, payer_grade FROM curated_mart.payer_scorecard ORDER BY denial_rate_pct DESC",
        x=0, y=12, w=24, h=8
    ),
    {
        "id": 8, "type": "barchart", "title": "AR Aging by Payer ($)",
        "gridPos": {"x": 0, "y": 20, "w": 14, "h": 8},
        "datasource": pg(),
        "options": {"xField": "payer_name", "stacking": "normal", "barWidth": 0.7, "orientation": "horizontal"},
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}, "overrides": []},
        "targets": [{
            "datasource": pg(), "format": "table", "rawQuery": True,
            "rawSql": 'SELECT payer_name, COALESCE(bucket_0_30,0) AS "0-30 days", COALESCE(bucket_31_60,0) AS "31-60 days", COALESCE(bucket_61_90,0) AS "61-90 days", COALESCE(bucket_90_plus,0) AS "90+ days" FROM curated_mart.ar_aging ORDER BY payer_name',
            "refId": "A"
        }]
    },
    pie_panel(
        9, "Recovery Category Breakdown",
        "SELECT recovery_category, COUNT(*) AS count FROM curated_curated.fct_denials GROUP BY recovery_category ORDER BY count DESC",
        x=14, y=20, w=10, h=8
    ),
]

dashboard = {
    "uid": "rcm-main",
    "title": "RCM Analytics Dashboard",
    "tags": ["rcm", "healthcare", "denials"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "5m",
    "panels": panels,
    "time": {"from": "now-1y", "to": "now"},
    "timepicker": {}
}

out = "/home/hc/hc-rcm-fhir-platform/grafana/dashboards/rcm-dashboard.json"
with open(out, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"dashboard written to {out}")
