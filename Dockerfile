FROM python:3.12


ENV PYTHONUNBUFFERED = 1
ENV PYTHONDONTWRITEBYTECODE=1


WORKDIR /

RUN apt-get update && apt-get install -y postgresql-client

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080