FROM python:3.13-bookworm AS builder
RUN apt-get update --yes --quiet \
 && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libgraphviz-dev \
 && rm -rf /var/lib/apt/lists/* \
 && python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /work
RUN pip install --upgrade pip build
COPY . .
RUN python -m build \
 && pip install gunicorn dist/*.whl

FROM python:3.13-slim-bookworm
ENV PATH=/opt/venv/bin:$PATH \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
RUN apt-get update --yes --quiet \
 && apt-get install --yes --quiet --no-install-recommends graphviz \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/pbdm_app
COPY --from=builder /opt/venv /opt/venv
CMD ["gunicorn", "pbdm_app.app:app"]
