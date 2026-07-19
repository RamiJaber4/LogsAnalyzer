FROM python:3.12-slim

WORKDIR /app

COPY frontend_server.py .
COPY index.html .

EXPOSE 8001

CMD ["python", "frontend_server.py"]