import json
import os
import time
from datetime import datetime, timezone

import clickhouse_connect
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensors/#")
CH_HOST = os.getenv("CH_HOST", "localhost")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
FLUSH_SECONDS = float(os.getenv("FLUSH_SECONDS", "5"))

ch = clickhouse_connect.get_client(host=CH_HOST)
buffer = []
last_flush = time.time()


def flush():
    global buffer, last_flush
    if buffer:
        ch.insert(
            "telemetry",
            buffer,
            column_names=["ts", "device_id", "metric", "value"],
        )
        buffer = []
    last_flush = time.time()


def on_message(client, userdata, msg):
    global last_flush
    try:
        payload = json.loads(msg.payload)
        device_id = msg.topic.split("/")[1]
        value = float(payload["value"])
        ts = datetime.fromtimestamp(payload.get("ts", time.time()), tz=timezone.utc)
        buffer.append([ts, device_id, payload.get("metric", "temperature"), value])
    except (ValueError, KeyError, json.JSONDecodeError):
        # We reject incomplete data; in the next version, it should ideally be stored in the error table.
        return

    if len(buffer) >= BATCH_SIZE or time.time() - last_flush >= FLUSH_SECONDS:
        flush()


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(MQTT_HOST, 1883)
client.subscribe(MQTT_TOPIC)
client.loop_forever()
