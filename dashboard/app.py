import datetime
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_mqtt import Mqtt
import time, queue, threading, html, json
import sqlite3

import git
#bioreactor_sim/nofaults/telemetry/summary

app = Flask(__name__)


app.config['MQTT_BROKER_URL'] = 'test.mosquitto.org'
app.config['MQTT_BROKER_URL'] = 'engf0001.cs.ucl.ac.uk'

app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your server supports TLS, set it True
topic = 'bioreactor_sim/three_faults/telemetry/summary'

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
    ts_start = data["window"]["start"]
    ts_end   = data["window"]["end"]

    db = sqlite3.connect("database.db")
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO reactor_summary (ts_start, ts_end, raw_json)
        VALUES (?, ?, ?)
    """, (
        ts_start,
        ts_end,
        json.dumps(data)
    ))

    db.commit()
    db.close()



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
    if rc == 0:
        print('Connected')
        mqtt_client.subscribe(topic)
        # mqtt_client.publish("bioreactor_group_3/set_points", '{"temperature_C": 32.0,"pH": 6.5,"rpm": 850.0}') # type: ignore
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

@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('path/to/git_repo')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


if __name__ == '__main__':
   app.run(host='127.0.0.1', port=5000, threaded=True, debug=True)
