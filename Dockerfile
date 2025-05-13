FROM python:3.13-bookworm AS builder
WORKDIR /work
RUN pip install --upgrade build
COPY . .
RUN python -m build

FROM python:3.13-slim-bookworm
ENV PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
WORKDIR /opt/pbdm_app
COPY --from=builder /work/dist/*.whl .
RUN pip install gunicorn *.whl
CMD ["gunicorn", "pbdm_app.app:app"]
