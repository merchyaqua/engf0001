# Dashboard Frontend Brief (HTML/JS & Charts)

The Flask backend (`dashboard/app.py`) is configured to receive telemetry over MQTT and expose it to the browser via Server-Sent Events (SSE). Next step is to build a browser-based dashboard (HTML + JavaScript) that consumes this SSE stream and presents it as a live log and charts.

## Setup Instructions
Ensure you have installed flask and flask-mqtt. 

```bash
flask run
```
## Files
app.py contains server logic to receive/publish MQTT.
dashboard.html contains code that has HTMX that listens to the server's published messages, and Javascript to format form data to send to the server via a POST request.


## Backend behaviour

- MQTT messages arrive on topic(s) under: `bioreactor_group_3/#`. Specifically `bioreactor_group_3/bioreactor_group_3/telemetry/summary` following the simulator format.
- Each MQTT payload is a JSON string, for example:

```json

{
    "window": {
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
}

{
    "window": {
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
}
```



- The server decodes this JSON in `handle_mqtt_message`, and enriches it with metadata:

  - `topic`: the MQTT topic string (e.g. `"bioreactor_group_3/telemetry/summary"`).
  - `timestamp`: ISO 8601 string generated server-side at receipt time.

- A typical successful message object pushed to the frontend looks like:

  ```json
    "window": {
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

  ```

- If there is a parsing error (e.g. non-JSON payload), the server sends a fallback object:

  ```json
  {
    "topic": "...",
    "raw_payload": "b'...'",
    "timestamp": "2025-03-21T12:34:56.789012",
    "error": "parse_failed"
  }
  ```

- The server exposes an SSE endpoint at `GET /events`. It sends:

  - An initial `retry: 1000` line to suggest a 1s reconnect delay.
  - The last known message (if any) as an SSE event named `"message"`.
  - Subsequent messages as `"message"` events, each formatted as:

    ```text
    event: message
    data: <JSON STRING>

    ```

- There is also a `GET /index` route that renders `dashboard/templates/dashboard.html`, and a `/publish` route that accepts JSON to send control setpoints back over MQTT. You should keep the existing control form and behaviour, but focus your changes on the display and plotting.

## What the frontend should implement

1. Replace the existing htmx-based SSE wiring with a native `EventSource` consuming `/events`.

2. Parse `event.data` as JSON and distinguish between good telemetry and error objects:

   - If `error === "parse_failed"`, display an appropriate warning in a log and do not add to charts.
   - Otherwise, treat the object as a valid telemetry sample.

3. Build a live “Messages” log:

   - Create a container (e.g. `<div id="messages"></div>`).
   - For each valid telemetry message, prepend a line showing timestamp, temperature, pH, and rpm. For example:
     - `2025-03-21T12:34:56Z T=32.0°C pH=6.5 rpm=850`.
   - For error messages, show something like:
     - `2025-03-21T12:34:56Z [parse_failed] <raw_payload>`.

4. Integrate a charting library (recommended: Chart.js via CDN):

   - Add a `<canvas id="telemetryChart"></canvas>` element.
   - Initialize a line chart with time on the x-axis (using the `timestamp` field) and one or more y-series:
     - At minimum, plot `temperature_C` over time.
     - Ideally, add separate lines/datasets for `pH` and `rpm` as well, with a clear legend.
   - On each SSE “message” event with valid telemetry, append the new point(s) to the datasets and call `chart.update()`.

5. Apply reasonable UI constraints:

   - Limit the number of points kept in memory and on the chart (e.g. last 500 samples).
   - Ensure the page remains responsive even under frequent updates.

6. Keep the existing control sliders and `/publish` POST logic intact, but visually differentiate control commands (what we request) from telemetry (what we receive). Only telemetry comes over SSE; controls are sent via fetch to `/publish`.

The key expectation is that the dashboard becomes a live monitoring page: as soon as the backend receives MQTT telemetry, the browser shows a textual log and continuously updating graphs, without any reloads.

