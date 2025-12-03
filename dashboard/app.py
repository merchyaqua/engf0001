import datetime
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_mqtt import Mqtt, ssl
import time, queue, threading, html, json
import sqlite3

#bioreactor_sim/nofaults/telemetry/summary

app = Flask(__name__)
BROKER = ""
PORT = 1883
TOPIC = ""
USERNAME = "group3"

broker_name = "hivemq"

match broker_name:
    case "test":
        BROKER = "test.mosquitto.org"   # public broker just to test connection
    case "ucl":
        BROKER = "engf0001.cs.ucl.ac.uk" # UCL broker for simulator data 

        TOPIC = "bioreactor_sim/single_fault/telemetry/summary"         

    case _:
        BROKER = "26063fe98ec0480d93ee20fbab5cf154.s1.eu.hivemq.cloud" # Non-UCL broker settings
        PORT = 8883
        USERNAME = "group3"
        PASSWORD = "Group3abc"
        TOPIC = "bioreactor_group_3/#"
        app.config['MQTT_USERNAME'] = USERNAME  # Set this item when you need to verify username and password
        app.config['MQTT_PASSWORD'] = PASSWORD  # Set this item when you need to verify username and password
        app.config['MQTT_TLS_ENABLED'] = True  # If your server supports TLS, set it True
        app.config['MQTT_TLS_CERT_REQS'] = ssl.CERT_REQUIRED
        app.config['MQTT_TLS_VERSION'] =ssl.PROTOCOL_TLS_CLIENT


app.config['MQTT_BROKER_URL'] = BROKER
app.config['MQTT_BROKER_PORT'] = PORT
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
topic = TOPIC
print(topic)

mqtt_client = Mqtt(app)

messages = []
    
# Per-client queues for SSE subscribers
subscribers = set()
subs_lock = threading.Lock()

def database_setup():
#         // Source - https://stackoverflow.com/a
#     // Posted by sjw
#     // Retrieved 2025-12-01, License - CC BY-SA 4.0


    with open('database.sql', 'r') as sql_file:
        sql_script = sql_file.read()

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.executescript(sql_script)
    db.commit()
    db.close()

database_setup()


def save(data):
    # ts_start = data["window"]["start"]
    # ts_end   = data["window"]["end"]

    # db = sqlite3.connect("database.db")
    # cursor = db.cursor()

    # cursor.execute("""
    #     INSERT INTO reactor_summary (ts_start, ts_end, raw_json)
    #     VALUES (?, ?, ?)
    # """, (
    #     ts_start,
    #     ts_end,
    #     json.dumps(data)
    # ))

    # db.commit()
    # db.close()
    print(data)
    return



def _broadcast(item):
    with subs_lock:
        for q in list(subscribers):
            try:
                q.put_nowait(item)
            except queue.Full:
                # Drop if a slow client backs up
                pass
# https://www.emqx.com/en/blog/how-to-use-mqtt-in-flask

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    sample_stream = '''    "window": {
        "start": 1763389772,
        "end": 1763389773,
        "seconds": 1,
        "samples": 11
    },
    "temperature_C": {
        "mean": 31.490105741201127,
        "min": 31.45392754641847,
        "max": 31.547580592169197
    },
    "pH": {
        "mean": 5.86476854225333,
        "min": 5.6901628909742525,
        "max": 6.0579492628174165
    },
    "rpm": {
        "mean": 852.1920684351512,
        "min": 831.4728702959867,
        "max": 885.2556326766498
    },
    "actuators_avg": {
        "heater_pwm": 0.44343035911546985,
        "motor_pwm": 0.7372140612716371,
        "acid_pwm": 0.0,
        "base_pwm": 0.004120351000476273
    },
    "dosing_l": {
        "acid": 5.247441644593267e-05,
        "base": 6.07093325782289e-05
    },
    "heater_energy_Wh": 0.01751615804208144,
    "photoevents": 32,
    "setpoints": {
        "temperature_C": 32.0,
        "pH": 6.5,
        "rpm": 850.0
    },
    "faults": {
        "last_active": [],
        "counts": {}
    }
'''
    print("tried to connect")
    if rc == 0:
        print('Connected')
        mqtt_client.subscribe(topic)
        # mqtt_client.publish("bioreactor_group_3/stream", '') # type: ignore
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
        mqtt_client.publish("bioreactor_group_3/telemetry/summary", sample) # type: ignore
        mqtt_client.publish("bioreactor_group_3/set_points", ) # type: ignore

    else:
        print("Bad connection ", rc)

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        data["topic"] = msg.topic
        data["timestamp"] = datetime.datetime.now().isoformat()

        save(data)
        _broadcast(data)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as e:
        print("Failed to parse MQTT payload:", e)
        fallback = {
            "topic": msg.topic,
            "raw_payload": repr(msg.payload),
            "timestamp": datetime.datetime.now().isoformat(),
            "error": "parse_failed",
        }
        messages.append(fallback)
        _broadcast(fallback)

@app.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.form.to_dict()
   topic = 'bioreactor_group_3/set_points'
   # Convert form data to JSON string for MQTT message
   import json
   msg = request.get_json()
   publish_result = mqtt_client.publish(topic, json.dumps(msg))
   return jsonify({'code': publish_result[0]})

@app.route('/index')
def index():
    return render_template("dashboard.html")

@app.route('/events')
def events():
    client_q = queue.Queue(maxsize=100)
    with subs_lock:
        subscribers.add(client_q)

    def gen():
        try:
            # Suggest 1s reconnect delay
            yield 'retry: 1000\n\n'
            # Send last known message immediately if available
            if messages:
                last = messages[-1]
                yield "event: message\ndata: " + json.dumps(last) + "\n\n"
            while True:
                try:
                    item = client_q.get(timeout=15)
                    yield "event: message\ndata: " + json.dumps(item) + "\n\n"

                except queue.Empty:
                    # Heartbeat to keep connection alive
                    yield ': keep-alive\n\n'
        finally:
            with subs_lock:
                subscribers.discard(client_q)

    headers = {
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }
    return Response(stream_with_context(gen()), mimetype='text/event-stream', headers=headers)



if __name__ == '__main__':
   app.run(host='127.0.0.1', port=5000, threaded=True, debug=True)
