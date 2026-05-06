# bptg (Blood Pressure To Garmin connect)

Docker container that bridges blood-pressure measurements from MQTT into
[Garmin Connect](https://connect.garmin.com).

Tested on Python 3.11.

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekdg) [!["PayPal.me"](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?business=LJ5ZF7Q9KMTRW&no_recurring=0&currency_code=USD)

</div>

## How it works

1. `bptg` subscribes to an MQTT topic carrying blood-pressure measurements
   (JSON with `Systolic`, `Diastolic`, `Pulse`, `TimeStamp`).
2. On startup it logs in to Garmin Connect once. Tokens (DI OAuth) are
   persisted to `/data/garminconnect` so subsequent restarts do not
   re-authenticate. This avoids Garmin rate-limits.
3. Every received message is parsed and uploaded via the `garminconnect`
   library. Duplicate / unavailable readings are skipped automatically.

## Get the image

Pre-built multi-arch images (`linux/amd64`, `linux/arm64`) are published
to GitHub Container Registry by GitHub Actions:

```bash
docker pull ghcr.io/mirecekd/bptg:latest
```

Available tags:

- `latest` — newest commit on `main`
- `vX.Y.Z` / `X.Y` — released versions
- `sha-<commit>` — exact commit

### Build locally (optional)

```bash
git clone https://github.com/mirecekd/bptg
cd bptg
docker build -t mirecekd/bptg .
```

## Run

Create a Docker volume for the persisted Garmin tokens (one-off):

```bash
docker volume create bptg_garmin_tokens
```

Run the container (replace values):

```bash
docker run -d \
  --name bptg \
  --restart unless-stopped \
  -e MQTT_BROKER=127.0.0.1 \
  -e MQTT_PORT=1883 \
  -e MQTT_USER=bptg \
  -e MQTT_PASS=bptg_secret \
  -e MQTT_TOPIC=miscale/USER/bp \
  -e MQTT_TTL=60 \
  -e GARMIN_USER=yourmail@domain.com \
  -e GARMIN_PASS=t0p53cr3t \
  -v bptg_garmin_tokens:/data/garminconnect \
  ghcr.io/mirecekd/bptg:latest
```

On the first start the container performs a credential login to Garmin
Connect and saves OAuth tokens into the volume. Every later restart (or
image upgrade) reuses those tokens and does not log in again.

> **Note:** Garmin accounts with MFA enabled are not currently supported
> by this container — credential login here is non-interactive.

### Synology

On a Synology NAS the same `docker run` command works over SSH. In
Container Manager just create a named volume / shared folder mount for
`/data/garminconnect`.

## Environment variables

| Variable             | Required | Default                | Description                                    |
|----------------------|:--------:|------------------------|------------------------------------------------|
| `MQTT_BROKER`        |    yes   | —                      | MQTT broker host                               |
| `MQTT_PORT`          |    yes   | —                      | MQTT broker port                               |
| `MQTT_USER`          |    yes   | —                      | MQTT username (also used as `client_id`)       |
| `MQTT_PASS`          |    yes   | —                      | MQTT password                                  |
| `MQTT_TOPIC`         |    yes   | —                      | Topic to subscribe                             |
| `MQTT_TTL`           |    yes   | —                      | MQTT keep-alive (seconds)                      |
| `GARMIN_USER`        |    yes   | —                      | Garmin Connect e-mail                          |
| `GARMIN_PASS`        |    yes   | —                      | Garmin Connect password                        |
| `GARMIN_TOKENSTORE`  |    no    | `/data/garminconnect`  | Directory used for persisted DI OAuth tokens   |
| `VERBOSE`            |    no    | `false`                | Set to `1`/`true` to enable DEBUG logging      |

## Expected MQTT payload

```json
{
  "TimeStamp": "2025-01-01 08:30:00",
  "Systolic": 120,
  "Diastolic": 80,
  "Pulse": 65
}
```

If any of `Systolic`/`Diastolic`/`Pulse` is the literal string
`"unavailable"`, the message is ignored.

## Support

If this project saves you time, consider buying me a coffee or sending a
tip — it helps keep things going.

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mirecekdg) [!["PayPal.me"](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?business=LJ5ZF7Q9KMTRW&no_recurring=0&currency_code=USD)

</div>

## License

MIT — see [LICENSE](LICENSE).
