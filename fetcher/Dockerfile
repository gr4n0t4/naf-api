FROM python:3.11-slim

COPY . /app
RUN pip install -r /app/requirements.txt
CMD [ "python", "/app/run.py" ]