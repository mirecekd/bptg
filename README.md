# bptg (Blood Pressure To Garmin connect)

Docker container to upload blood pressure data from MQTT to https://connect.garmin.com. 

Tested on Python 3.11 

## Build image:

clone this repo and build container
```
git clone https://github.com/mirecekd/bptg
cd bptg
docker build -t mirecekd/bptg .
```

## Run container:
(use your values)


```
docker run --name=bptg \
  -e "MQTT_BROKER=127.0.0.1" \
  -e "MQTT_PORT=1883" \
  -e "MQTT_USER=bptg" \
  -e "MQTT_PASS=bptg_secret" \
  -e "MQTT_TOPIC=miscale/USER/bp" \
  -e "MQTT_TTL=60" \
  -e "GARMIN_USER=yourmail@domain.com" \
  -e "GARMIN_PASS=t0p53cr3t" \
  --restart always \
  mirecekd/bptg
```
## Workflow

1. bptg reads MQTT topic and pushes data to Garmin Connect
