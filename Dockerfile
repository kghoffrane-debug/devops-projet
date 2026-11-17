ARG PYTHON_VERSION=3.12

# Étape 1 : installer les dépendances
FROM python:${PYTHON_VERSION}-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Étape 2 : image finale légère
FROM python:${PYTHON_VERSION}-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app.py .
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
EXPOSE 5000
CMD ["python", "app.py"]