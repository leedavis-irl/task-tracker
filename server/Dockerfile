FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

RUN mkdir -p /data

ENV STATE_FILE=/data/state.json
ENV EC2_RELAY_URL=http://127.0.0.1:8766/send-signal
ENV RELAY_TOKEN=CHANGE_ME_shared_secret

EXPOSE 8765

CMD ["python", "server.py"]
