FROM python:3.12-slim

ARG GATEWAY_PORT

WORKDIR /app

COPY gateway/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY gateway/ .

COPY contracts/auth_service/ .

EXPOSE ${GATEWAY_PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${GATEWAY_PORT} --reload"]

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$GATEWAY_PORT", "--reload"]

# CMD [python3, config.py]