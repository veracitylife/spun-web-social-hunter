FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY social_hunter ./social_hunter

EXPOSE 8000

CMD ["uvicorn", "social_hunter.main:app", "--host", "0.0.0.0", "--port", "8000"]

