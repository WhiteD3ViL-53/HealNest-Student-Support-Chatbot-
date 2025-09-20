FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/launcher.sh

ENV PORT=8080

CMD ["/app/launcher.sh"]
