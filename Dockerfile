FROM onsdigital/flask-crypto

ADD server.py /app/server.py
ADD settings.py /app/settings.py
ADD queue_publisher.py /app/queue_publisher.py
ADD requirements.txt /app/requirements.txt
ADD startup.sh /app/startup.sh

RUN mkdir -p /app/logs

RUN apt-get update
RUN apt-get install -y python3-dev
RUN apt-get install -y libpq-dev
RUN apt-get install -y build-essential

# set working directory to /app/
WORKDIR /app/

EXPOSE 5000

RUN pip3 install --no-cache-dir -U -I -r /app/requirements.txt

ENTRYPOINT ./startup.sh
