FROM python:3.12-slim

ARG GATEWAY_PORT

ARG AUTH_PORT
ENV AUTH_PORT=$AUTH_PORT

ARG NOTIFICATION_PORT
ENV NOTIFICATION_PORT=$NOTIFICATION_PORT

WORKDIR /app

COPY gateway/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY contracts/auth_service/ .
COPY contracts/notification_service/ .

EXPOSE ${GATEWAY_PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${GATEWAY_PORT} --reload"]
