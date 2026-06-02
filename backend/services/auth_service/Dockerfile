FROM python:3.12-slim

ARG AUTH_SERVICE_PORT

WORKDIR /app

ENV PYTHONPATH=/app/app
ENV AUTH_SERVICE_PORT=${AUTH_SERVICE_PORT}

COPY services/auth_service/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY services/auth_service ./app
COPY shared/protos ./protos

RUN mkdir -p /app/logs
RUN python -m grpc_tools.protoc \
    -I /app/protos/auth_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/auth_service/*.proto
RUN python -m grpc_tools.protoc \
    -I /app/protos/notification_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/notification_service/*.proto

RUN chmod +x ./app/scripts/entrypoint.sh

EXPOSE ${AUTH_SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os, grpc, auth_service_pb2, auth_service_pb2_grpc; channel=grpc.insecure_channel('127.0.0.1:'+os.getenv('AUTH_SERVICE_PORT','5534')); response=auth_service_pb2_grpc.AuthServiceStub(channel).HealthCheck(auth_service_pb2.HealthCheckRequest(), timeout=3); raise SystemExit(0 if response.success else 1)"

ENTRYPOINT ["./app/scripts/entrypoint.sh"]
