"""Motor determinístico de cenários; sem alteração de modelos ou de preços reais."""
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
from pricing.artifacts import ArtifactCatalog
from pricing.schemas import SimulationRequest, SimulationResult, Scenario

CENT = Decimal('.01')
DISCLAIMER = 'Resposta ao preço experimental e observacional; não comprova causalidade nem ganho real de receita.'

def candidate_prices(request: SimulationRequest) -> list[Decimal]:
    current = request.current_price
    lo = current * (1 - Decimal(str(request.max_decrease_pct))/100)
    hi = current * (1 + Decimal(str(request.max_increase_pct))/100)
    candidates = {current}
    for sign, maximum in [(-1, request.max_decrease_pct), (1, request.max_increase_pct)]:
        end, step = Decimal(str(maximum)), Decimal(str(request.step_pct))
        changes = {end}
        value = step
        while value < end:
            changes.add(value)
            value += step
        for change in changes:
            p = (current*(1+Decimal(sign)*change/100)).quantize(CENT, rounding=ROUND_HALF_UP)
            # Ajusta para o centavo viável mais próximo sem ultrapassar o limite.
            if p < lo:
                p = lo.quantize(CENT, rounding=ROUND_CEILING)
            if p > hi:
                p = hi.quantize(CENT, rounding=ROUND_FLOOR)
            if p >= CENT and lo <= p <= hi:
                candidates.add(p)
    return sorted(candidates)

def money(value):
    return float(Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP))

def simulate(request: SimulationRequest, catalog: ArtifactCatalog) -> SimulationResult:
    product = catalog.get_product(request.product_id)
    current = float(request.current_price)
    week = None
    warnings = [DISCLAIMER, 'Sem estoque, custos ou concorrência históricos: estoque é informado e receita não representa lucro.',
                'O fator foi estimado em semanas com vendas; sua aplicação à demanda-base de todas as semanas é uma hipótese não validada.']
    if request.demand_source == 'manual':
        base = request.base_demand
        warnings.append('Demanda-base semanal informada pelo usuário; não é uma previsão produzida pelo modelo.')
    else:
        snapshot = catalog.get_snapshot(request.product_id, request.reference_week)
        base, week = snapshot['base_demand'], snapshot['week']
        warnings.append(f'MovingAverage4 histórico com referência em {week}; dados antigos da Olist, não demanda atual. Histórico considera entregas já confirmadas e pode subestimar vendas recentes.')
    if not product['sufficient_individual_support']:
        warnings.append('Suporte individual insuficiente: aplicada apenas a elasticidade compartilhada experimental, não uma curva validada deste produto.')
    else:
        warnings.append('O produto passa a triagem mínima de variação histórica; isso não valida sua elasticidade individual. Usa-se a elasticidade compartilhada.')
    scenarios = []
    for price in candidate_prices(request):
        p = float(price)
        factor = (p/current)**catalog.beta
        adjusted = base*factor
        sellable = min(adjusted, request.stock)
        outside = p < product['min_price'] or p > product['max_price']
        flags = []
        if outside:
            flags.append('Preço fora da faixa histórica observada no treino deste produto.')
        if not product['sufficient_individual_support']:
            flags.append('Suporte individual insuficiente; resposta compartilhada experimental.')
        scenarios.append(Scenario(price=p, change_pct=round((p/current-1)*100, 6),
                                  response_factor=factor, adjusted_demand=adjusted, sellable_units=sellable,
                                  estimated_revenue=money(p*sellable), outside_historical_range=outside, warnings=flags))
    # Empate de receita em centavos: prefere menor alteração, preservando preço atual.
    best = min(scenarios, key=lambda s: (-s.estimated_revenue, abs(s.price-current), s.price))
    now = next(s for s in scenarios if s.price == current)
    outside_count = sum(s.outside_historical_range for s in scenarios)
    if outside_count:
        warnings.append(f'{outside_count} de {len(scenarios)} preços candidatos estão fora da faixa histórica do produto. A comparação inclui essas extrapolações, marcadas na tabela.')
    if best.outside_historical_range:
        warnings.append('O preço recomendado está fora da faixa histórica: resultado apenas hipotético, sem validação nesse preço.')
    if request.stock == 0:
        warnings.append('Estoque zero: receita estimada zero; preço atual preservado no empate.')
    if base == 0:
        warnings.append('Demanda-base zero: nenhum ganho estimado; preço atual preservado no empate.')
    if len(scenarios) == 1:
        warnings.append('Somente o preço atual é viável com estes limites e arredondamento em centavos.')
    return SimulationResult(product_id=request.product_id, category=product['category'], current_price=current,
                            recommended_price=best.price, change_pct=best.change_pct, base_demand=base,
                            demand_source=request.demand_source, demand_reference_week=week,
                            adjusted_demand=best.adjusted_demand, stock=request.stock, sellable_units=best.sellable_units,
                            current_estimated_revenue=now.estimated_revenue, recommended_estimated_revenue=best.estimated_revenue,
                            estimated_revenue_change_pct=round((best.estimated_revenue/now.estimated_revenue-1)*100,6) if now.estimated_revenue>0 else None,
                            elasticity=catalog.beta, historical_price_range={'min':product['min_price'],'max':product['max_price']},
                            sufficient_individual_support=product['sufficient_individual_support'], scenarios=scenarios,
                            warnings=warnings, artifact_versions=dict(catalog.versions))
