FROM python:3.12-slim

ARG GATEWAY_PORT=8000

WORKDIR /app

ENV PYTHONPATH=/app/app
ENV GATEWAY_PORT=${GATEWAY_PORT}

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY shared/protos ./protos

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
RUN python -m grpc_tools.protoc \
    -I /app/protos/booking_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/booking_service/*.proto
RUN python -m grpc_tools.protoc \
    -I /app/protos/schedule_service \
    --python_out=/app/app \
    --grpc_python_out=/app/app \
    /app/protos/schedule_service/*.proto

EXPOSE ${GATEWAY_PORT}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('GATEWAY_PORT','8000')+'/health', timeout=3).read()"

CMD ["sh", "-c", "uvicorn main:app --host ${GATEWAY_HOST:-0.0.0.0} --port ${GATEWAY_PORT:-8000}"]
