FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements-app.txt ./
RUN pip install --no-cache-dir -r requirements-app.txt
COPY pricing/ ./pricing/
COPY .streamlit/ ./.streamlit/
COPY artifacts/product/chosen_model.joblib ./artifacts/product/chosen_model.joblib
COPY artifacts/price_response/loglog.json ./artifacts/price_response/loglog.json
COPY reports/price_response/individual_support.csv ./reports/price_response/individual_support.csv
COPY data/processed/product_week_features.csv ./data/processed/product_week_features.csv
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/runtime && chown appuser:appuser /app/runtime
USER appuser
EXPOSE 8000 8501
CMD ["python", "-m", "uvicorn", "pricing.api:app", "--host", "0.0.0.0", "--port", "8000"]
