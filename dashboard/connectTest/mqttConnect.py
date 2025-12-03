import paho.mqtt.client as paho
from paho import mqtt
import json

BROKER = ""
PORT = 1883
TOPIC = ""
USERNAME = "group3"


broker_name = "nonucl"

match broker_name:
    case "test":
        BROKER = "test.mosquitto.org"   # public broker just to test connection
    case "ucl":
        BROKER = "engf0001.cs.ucl.ac.uk" # UCL broker for simulator data 

        TOPIC = "bioreactor_sim/single_fault/telemetry/summary"         

    case nonucl:
        BROKER = "26063fe98ec0480d93ee20fbab5cf154.s1.eu.hivemq.cloud" # Non-UCL broker settings
        PORT = 8883
        USERNAME = "group3"
        PASSWORD = "Group3abc"
        TOPIC = "bioreactor_group_3/#"



historical_data = []

def save(topic, data) :
    historical_data.append(data)

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code", rc)
    sample = '''

{
    "temperature_C": {
        "mean": 31.490105741201127
    },
    "pH": {
        "mean": 5.86476854225333
    },
    "rpm": {
        "mean": 852.1920684351512
    }
}'''
    client.subscribe(TOPIC)
    client.publish("bioreactor_group_3/set_points", sample) # type: ignore


def on_message(client, userdata, msg):
    # The payload is a byte string, so we decode it to a regular string
    decoded_payload = msg.payload.decode("utf-8")
    # Convert JSON string to dictionary
    
    data = json.loads(decoded_payload)
    print(type(data))

    print(f"[{msg.topic}] {data}")
    save(msg.topic, data)

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)

if broker_name == "nonucl":
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(cert_reqs=paho.ssl.CERT_REQUIRED, tls_version=paho.ssl.PROTOCOL_TLS_CLIENT)
client.connect(BROKER, PORT, 60)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = lambda client, userdata, mid: print("mid: "+str(mid))


client.loop_forever()
