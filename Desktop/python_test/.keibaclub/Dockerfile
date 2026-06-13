FROM python:3.13-slim
WORKDIR /app
COPY app.py .
COPY keiba_club.db .
COPY static/ static/
EXPOSE 8000
CMD ["python", "app.py"]
