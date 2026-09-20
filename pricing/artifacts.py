"""Somente leitura dos artefatos congelados; nenhum treino na aplicação."""
import csv
import hashlib
import json
import math
from pathlib import Path
import joblib

ROOT = Path(__file__).resolve().parents[1]

class ArtifactCatalog:
    def __init__(self, root: Path = ROOT):
        paths = {
            'demand_model_sha256': root/'artifacts/product/chosen_model.joblib',
            'price_response_sha256': root/'artifacts/price_response/loglog.json',
            'support_sha256': root/'reports/price_response/individual_support.csv',
            'history_sha256': root/'data/processed/product_week_features.csv',
        }
        self.versions = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
        # Apenas arquivo local confiável produzido pelo projeto; nunca recebe upload.
        champion = joblib.load(paths['demand_model_sha256'])
        if champion['name'] != 'MovingAverage4' or champion['baseline_feature'] != 'units_mean_4w':
            raise ValueError('Artefato de demanda incompatível: MovingAverage4 esperado.')
        self.versions.update(demand_model='MovingAverage4', price_response='LogLogPooled', app='1.0.0')
        response = json.loads(paths['price_response_sha256'].read_text())
        self.beta = float(response['beta'])
        if not math.isfinite(self.beta):
            raise ValueError('Elasticidade inválida no artefato.')
        self.elasticity_interval = response['cluster_bootstrap_95pct']
        self.products = {}
        with paths['support_sha256'].open() as f:
            for row in csv.DictReader(f):
                self.products[row['entity_id']] = {
                    'product_id': row['entity_id'], 'category': row['category'],
                    'min_price': float(row['min_price']), 'max_price': float(row['max_price']),
                    'sufficient_individual_support': row['eligible_individual_slope'].lower() == 'true',
                    'active_train_weeks': int(row['active_train_weeks']),
                    'weekly_prices': int(row['weekly_prices']),
                }
        self.history = {pid: [] for pid in self.products}
        with paths['history_sha256'].open() as f:
            for row in csv.DictReader(f):
                if row['entity_id'] not in self.history or not row['units_mean_4w']:
                    continue
                demand = float(row['units_mean_4w'])
                if not math.isfinite(demand) or demand < 0:
                    continue
                price = float(row['last_observed_price']) if row['last_observed_price'] else None
                self.history[row['entity_id']].append({
                    'week': row['week'][:10], 'base_demand': demand,
                    'last_observed_price': price,
                })
        for pid, rows in self.history.items():
            rows.sort(key=lambda r: r['week'])
            latest = rows[-1] if rows else None
            self.products[pid]['latest_snapshot'] = latest
        if not self.products or not any(self.history.values()):
            raise ValueError('Catálogo ou histórico vazio.')

    def get_product(self, pid):
        if pid not in self.products:
            raise KeyError('Produto não encontrado no catálogo elegível.')
        return self.products[pid]

    def get_snapshot(self, pid, week=None):
        self.get_product(pid)
        rows = self.history[pid]
        if week is not None:
            rows = [row for row in rows if row['week'] == week.isoformat()]
        if not rows:
            raise ValueError('Não há histórico MovingAverage4 para a semana informada.')
        return rows[-1]
