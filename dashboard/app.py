from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_mqtt import Mqtt
import time, queue, threading, html

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = 'engf0001.cs.ucl.ac.uk'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your server supports TLS, set it True
topic = 'bioreactor_sim/nofaults/telemetry/summary'

mqtt_client = Mqtt(app)

messages = []
# Per-client queues for SSE subscribers
subscribers = set()
subs_lock = threading.Lock()

def _broadcast(item: str):
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
    else:
        print("Bad connection ", rc)

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, msg):
    try:
        text = f"[{msg.topic}] {msg.payload.decode()}"
        messages.append(text)
        _broadcast(text)
    except UnicodeDecodeError:
        # print("Can't decode")
        pass



@app.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   return jsonify({'code': publish_result[0]})

@app.route('/index')
def index():
    return render_template("dashboard.html")

@app.route('/events')
def events():
    client_q = queue.Queue(maxsize=100)
    with subs_lock:
        subscribers.add(client_q)

    def _render(text: str) -> str:
        return f'<div class="message">{html.escape(text)}</div>'

    def gen():
        try:
            # Suggest 1s reconnect delay
            yield 'retry: 1000\n\n'
            # Send last known message immediately if available
            if messages:
                yield f"event: message\ndata: {_render(messages[-1])}\n\n"
            while True:
                try:
                    item = client_q.get(timeout=15)
                    yield f"event: message\ndata: {_render(item)}\n\n"

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
