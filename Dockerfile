FROM onsdigital/flask-crypto

ADD server.py /app/server.py
ADD settings.py /app/settings.py
ADD requirements.txt /app/requirements.txt
ADD startup.sh /app/startup.sh

RUN mkdir -p /app/logs

# set working directory to /app/
WORKDIR /app/

EXPOSE 5000

RUN pip3 install --no-cache-dir -U -I -r /app/requirements.txt

ENTRYPOINT ./startup.sh
