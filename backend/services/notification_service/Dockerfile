FROM python:3.12-slim

ARG NOTIFICATION_SERVICE_PORT=5533

WORKDIR /app

ENV PYTHONPATH=/app/app
ENV NOTIFICATION_SERVICE_PORT=${NOTIFICATION_SERVICE_PORT}

COPY services/notification_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/notification_service ./app
COPY shared/protos ./protos

RUN mkdir -p /app/logs
RUN python -m grpc_tools.protoc \
    -I /app/protos/notification_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/notification_service/*.proto

RUN chmod +x /app/app/scripts/entrypoint.sh

EXPOSE ${NOTIFICATION_SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os, grpc, notification_service_pb2, notification_service_pb2_grpc; channel=grpc.insecure_channel('127.0.0.1:'+os.getenv('NOTIFICATION_SERVICE_PORT','5533')); response=notification_service_pb2_grpc.NotificationServiceStub(channel).HealthCheck(notification_service_pb2.HealthCheckRequest(), timeout=3); raise SystemExit(0 if response.success else 1)"

ENTRYPOINT ["/app/app/scripts/entrypoint.sh"]
