FROM python:3.12-slim

ARG NOTIFICATION_HOST
ARG NOTIFICATION_PORT

ENV NOTIFICATION_HOST=$NOTIFICATION_HOST
ENV NOTIFICATION_PORT=$NOTIFICATION_PORT

WORKDIR /app

COPY notification_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY notification_service/ .

COPY contracts/notification_service/ .

EXPOSE $NOTIFICATION_PORT

# CMD ["python", "-m", "notification_service"]

CMD ["python", "-m", "notification_service"]
