mqttConnect.py contains code for setting up a connection and saving all received data into a list.
app.py is for the web backend and dashboard.html is for the web frontend.

Topic: [bioreactor_group_3/telemetry/summary] 
Subscribed to by: client
Publisher: ESP32
Arduino: communicate sensor data to ESP32
ESP32: format it as JSON, publish to the topic.
time format: ISO string

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
}


Topic: [bioreactor_group_3/set_points] 
Subscribed to by: ESP32
Publisher: client

Payload: ```json
{
    "temperature_C": 32.0,
    "pH": 6.5,
    "rpm": 850.0
} ```
ESP32: on receiving message from the set points topic, it should communicate this to the Arduino.
Arduino: listens for set point changes from the ESP32, so subsystems adjust.

