FROM python:3.12-slim

ARG SCHEDULE_SERVICE_PORT=5536

WORKDIR /app

ENV PYTHONPATH=/app/app
ENV SCHEDULE_SERVICE_PORT=${SCHEDULE_SERVICE_PORT}

COPY services/schedule_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/schedule_service ./app
COPY shared/protos ./protos

RUN mkdir -p /app/logs
RUN python -m grpc_tools.protoc \
    -I /app/protos/schedule_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/schedule_service/*.proto
RUN python -m grpc_tools.protoc \
    -I /app/protos/booking_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/booking_service/*.proto
RUN python -m grpc_tools.protoc \
    -I /app/protos/auth_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/auth_service/*.proto

RUN chmod +x /app/app/scripts/entrypoint.sh

EXPOSE ${SCHEDULE_SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os, grpc, schedule_service_pb2, schedule_service_pb2_grpc; channel=grpc.insecure_channel('127.0.0.1:'+os.getenv('SCHEDULE_SERVICE_PORT','5536')); response=schedule_service_pb2_grpc.ScheduleServiceStub(channel).HealthCheck(schedule_service_pb2.HealthCheckRequest(), timeout=3); raise SystemExit(0 if response.success else 1)"

ENTRYPOINT ["/app/app/scripts/entrypoint.sh"]
