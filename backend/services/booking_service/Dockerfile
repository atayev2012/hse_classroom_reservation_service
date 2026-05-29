FROM python:3.12-slim

ARG BOOKING_SERVICE_PORT=5535

WORKDIR /app

ENV PYTHONPATH=/app/app
ENV BOOKING_SERVICE_PORT=${BOOKING_SERVICE_PORT}

COPY services/booking_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/booking_service ./app
COPY shared/protos ./protos

RUN mkdir -p /app/logs
RUN python -m grpc_tools.protoc \
    -I /app/protos/booking_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/booking_service/*.proto

RUN chmod +x /app/app/scripts/entrypoint.sh

EXPOSE ${BOOKING_SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os, grpc, booking_service_pb2, booking_service_pb2_grpc; channel=grpc.insecure_channel('127.0.0.1:'+os.getenv('BOOKING_SERVICE_PORT','5535')); response=booking_service_pb2_grpc.BookingServiceStub(channel).HealthCheck(booking_service_pb2.HealthCheckRequest(), timeout=3); raise SystemExit(0 if response.success else 1)"

ENTRYPOINT ["/app/app/scripts/entrypoint.sh"]
