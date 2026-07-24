FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV MOCK_MCP_HOST=0.0.0.0
ENV MOCK_MCP_PORT=9100
EXPOSE 9100

CMD ["python", "app/server.py"]
