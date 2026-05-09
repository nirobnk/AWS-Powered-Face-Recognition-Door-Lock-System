import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv('MQTT_BROKER', '127.0.0.1')
PORT   = int(os.getenv('MQTT_PORT', 1883))
TOPIC  = os.getenv('MQTT_TOPIC', 'door/command')


def publish_command(command: str):
    """
    Publishes UNLOCK or DENY to the MQTT broker.
    The ESP32 is subscribed to this topic and will act on it.
    QoS 1 = guaranteed at-least-once delivery.
    """
    try:
        client = mqtt.Client(client_id="door-backend")
        client.connect(BROKER, PORT, keepalive=10)
        client.publish(TOPIC, payload=command, qos=1)
        client.disconnect()
        print(f"[MQTT] Published: {command}  →  {TOPIC}")
    except Exception as e:
        print(f"[MQTT] Error publishing command: {e}")