FROM ubuntu:16.04
ENV RUNTIME_PACKAGES="python3"
ENV BUILD_PACKAGES="git curl build-essential python3-dev ca-certificates libssl-dev libffi-dev postgresql libpq-dev"

ADD server.py /app/server.py
ADD settings.py /app/settings.py
ADD queue_publisher.py /app/queue_publisher.py
ADD requirements.txt /app/requirements.txt
ADD startup.sh /app/startup.sh
RUN mkdir -p /app/logs

# set working directory to /app/
WORKDIR /app/
EXPOSE 5000

RUN apt-get update && apt-get install -y $RUNTIME_PACKAGES $BUILD_PACKAGES && curl -sS https://bootstrap.pypa.io/get-pip.py | python3

RUN git clone https://github.com/ONSdigital/sdx-common.git
RUN pip3 install ./sdx-common
RUN pip3 install --no-cache-dir -U -r /app/requirements.txt

ENTRYPOINT ./startup.sh
