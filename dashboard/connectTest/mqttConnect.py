import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"   # public broker
BROKER = 'engf0001.cs.ucl.ac.uk'
PORT = 1883
TOPIC = "#"             # feel free to change

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    print(f"[{msg.topic}] {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()
