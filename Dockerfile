# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9.11

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install curl or wget (if not already included in the base image)
RUN apt-get update && apt-get install -y curl

# Download the model file from GitHub release
RUN curl -LJO https://github.com/EriSetyawan166/ScanCare-Modelling/releases/download/transfer-learning-mobilenetv2-v1.0/model.h5


# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
