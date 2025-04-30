FROM python:3.13-alpine
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# CMD ["fastapi", "run", "api/main.py", "--port", "80"]

CMD ["uvicorn", "main:app", "--workers", "4", "--host", "0.0.0.0", "--port", "3000"]