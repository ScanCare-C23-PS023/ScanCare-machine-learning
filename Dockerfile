FROM python:3.9.11

# Create app directory
WORKDIR /flask-testing-for-md

# Bundle app source
COPY . .

RUN apt-get update

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT [ "python" ]
CMD [ "app.py" ]