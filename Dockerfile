FROM onsdigital/flask-crypto-queue

ENTRYPOINT ./startup.sh

COPY server.py /app/server.py
COPY settings.py /app/settings.py
COPY requirements.txt /app/requirements.txt
COPY startup.sh /app/startup.sh
COPY Makefile /app/Makefile
RUN mkdir -p /app/logs

# set working directory to /app/
WORKDIR /app/
EXPOSE 5000

RUN make build

