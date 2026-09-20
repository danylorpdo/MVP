import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Query
from pricing import __version__
from pricing.artifacts import ArtifactCatalog, ROOT
from pricing.engine import simulate
from pricing.schemas import SimulationRequest, SavedSimulation
from pricing.storage import SimulationStore

def create_app(catalog=None, db_path=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.catalog = catalog if catalog is not None else ArtifactCatalog()
        app.state.store = SimulationStore(db_path or os.getenv('PRICING_DB_PATH', str(ROOT/'runtime/simulations.sqlite')))
        yield

    app = FastAPI(title='Pricing Lab — Marketplace', version=__version__,
                  description='Simulação acadêmica observacional de preços. Não altera ofertas reais.', lifespan=lifespan)

    @app.get('/health', tags=['Status'])
    def health():
        try:
            with app.state.store.connect() as con:
                con.execute('SELECT 1').fetchone()
        except sqlite3.Error:
            raise HTTPException(503, 'Persistência indisponível.')
        return {'status':'ok', 'version':__version__, 'demand_model':'MovingAverage4', 'price_response':'LogLogPooled'}

    @app.get('/api/v1/metadata', tags=['Catálogo'])
    def metadata():
        c = app.state.catalog
        return {'elasticity':c.beta, 'elasticity_interval':c.elasticity_interval, 'artifact_versions':c.versions,
                'price_change_limit_pct':10, 'horizon':'uma semana', 'experimental':True}

    @app.get('/api/v1/products', tags=['Catálogo'])
    def products():
        return sorted(app.state.catalog.products.values(), key=lambda p:(p['category'],p['product_id']))

    @app.get('/api/v1/products/{product_id}/history', tags=['Catálogo'])
    def history(product_id: str):
        try:
            app.state.catalog.get_product(product_id)
        except KeyError as e:
            raise HTTPException(404, e.args[0])
        return app.state.catalog.history[product_id]

    @app.post('/api/v1/simulations', response_model=SavedSimulation, status_code=201, tags=['Simulações'])
    def run_simulation(request: SimulationRequest):
        try:
            result = simulate(request, app.state.catalog)
        except KeyError as e:
            raise HTTPException(404, e.args[0])
        except ValueError as e:
            raise HTTPException(422, str(e))
        saved = SavedSimulation(**result.model_dump(), id=str(uuid4()), created_at=datetime.now(timezone.utc).isoformat())
        try:
            app.state.store.save(request.model_dump(mode='json'), saved.model_dump(mode='json'))
        except sqlite3.Error:
            raise HTTPException(503, 'Não foi possível salvar a simulação. Tente novamente.')
        return saved

    @app.get('/api/v1/simulations', tags=['Simulações'])
    def list_simulations(limit: int = Query(20,ge=1,le=100)):
        try:
            return app.state.store.list(limit)
        except sqlite3.Error:
            raise HTTPException(503, 'Não foi possível consultar o histórico. Tente novamente.')

    @app.get('/api/v1/simulations/{simulation_id}', tags=['Simulações'])
    def get_simulation(simulation_id: str):
        try:
            result = app.state.store.get(simulation_id)
        except sqlite3.Error:
            raise HTTPException(503, 'Não foi possível consultar a simulação. Tente novamente.')
        if result is None:
            raise HTTPException(404,'Simulação não encontrada.')
        return result
    return app

app = create_app()
