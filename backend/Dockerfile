FROM python:3.10-slim-buster

WORKDIR /app
RUN pip install gunicorn==23.0.0
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
COPY data/ingredients.csv /app/data/ingredients.csv
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]

