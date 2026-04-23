FROM python:3.12-slim

ARG AUTH_PORT

WORKDIR /app

COPY auth_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY auth_service/ .

COPY contracts/auth_service/ .

EXPOSE $AUTH_PORT

CMD ["python", "auth_service.py"]
