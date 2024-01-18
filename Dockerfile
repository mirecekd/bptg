FROM python:3.11-alpine

RUN pip install paho-mqtt garminconnect

WORKDIR /opt/bptg

COPY bptg.py /opt/bptg

COPY entrypoint.sh /
COPY cmd.sh /

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
