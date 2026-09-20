from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    product_id: str = Field(min_length=1, max_length=64)
    current_price: Decimal = Field(gt=0, le=Decimal('1000000000'), max_digits=12, decimal_places=2)
    stock: Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]
    demand_source: Literal['manual', 'moving_average4'] = 'manual'
    base_demand: float | None = Field(default=None, ge=0, le=1_000_000_000)
    reference_week: date | None = None
    max_decrease_pct: float = Field(default=10, ge=0, le=10)
    max_increase_pct: float = Field(default=10, ge=0, le=10)
    step_pct: float = Field(default=5, ge=.1, le=10)

    @model_validator(mode='after')
    def demand_contract(self):
        if self.demand_source == 'manual':
            if self.base_demand is None:
                raise ValueError('Informe a demanda base no modo manual.')
            if self.reference_week is not None:
                raise ValueError('Semana histórica só é usada no modo MovingAverage4.')
        elif self.base_demand is not None:
            raise ValueError('No modo MovingAverage4, não envie demanda manual.')
        return self

class Scenario(BaseModel):
    price: float
    change_pct: float
    response_factor: float
    adjusted_demand: float
    sellable_units: float
    estimated_revenue: float
    outside_historical_range: bool
    warnings: list[str]

class SimulationResult(BaseModel):
    product_id: str
    category: str
    current_price: float
    recommended_price: float
    change_pct: float
    base_demand: float
    demand_source: str
    demand_reference_week: str | None
    horizon: str = 'uma semana'
    adjusted_demand: float
    stock: int
    sellable_units: float
    current_estimated_revenue: float
    recommended_estimated_revenue: float
    estimated_revenue_change_pct: float | None
    elasticity: float
    historical_price_range: dict[str, float]
    sufficient_individual_support: bool
    scenarios: list[Scenario]
    warnings: list[str]
    artifact_versions: dict[str, str]
    methodology: str = 'simulação observacional experimental; não causal'

class SavedSimulation(SimulationResult):
    id: str
    created_at: str
