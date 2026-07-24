FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

RUN groupadd --system easyorder && useradd --system --gid easyorder --create-home easyorder

WORKDIR /app

COPY --from=builder /root/.local /home/easyorder/.local
COPY app ./app

RUN chown -R easyorder:easyorder /app
USER easyorder

ENV PATH=/home/easyorder/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
