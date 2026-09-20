import json
import sqlite3
from pathlib import Path

class SimulationStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('CREATE TABLE IF NOT EXISTS simulations (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, product_id TEXT NOT NULL, request_json TEXT NOT NULL, result_json TEXT NOT NULL)')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def save(self, request, result):
        with self.connect() as con:
            con.execute('INSERT INTO simulations VALUES (?, ?, ?, ?, ?)',
                        (result['id'], result['created_at'], result['product_id'], json.dumps(request), json.dumps(result)))

    def list(self, limit=20):
        with self.connect() as con:
            rows = con.execute('SELECT id, created_at, product_id, result_json FROM simulations ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
        return [{'id':r[0], 'created_at':r[1], 'product_id':r[2], 'current_price':json.loads(r[3])['current_price'], 'recommended_price':json.loads(r[3])['recommended_price'], 'recommended_estimated_revenue':json.loads(r[3])['recommended_estimated_revenue']} for r in rows]

    def get(self, simulation_id):
        with self.connect() as con:
            row = con.execute('SELECT request_json, result_json FROM simulations WHERE id = ?', (simulation_id,)).fetchone()
        return {'request':json.loads(row[0]), 'result':json.loads(row[1])} if row else None
