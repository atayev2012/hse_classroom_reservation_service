FROM python:3.12-slim

WORKDIR /app

COPY auth_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY auth_service/ .

COPY contracts/auth_service/ .

EXPOSE 5050

CMD ["python", "auth_service.py"]
