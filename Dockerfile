FROM python:3.12-slim

#create work directory on the container
WORKDIR /app

#Copy current directory content into the container directory /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
