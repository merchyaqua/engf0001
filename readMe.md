mqttConnect.py contains code for setting up a connection and saving all received data into a list.
app.py is for the web backend and dashboard.html is for the web frontend.

Topic: [bioreactor_group_3/telemetry/summary] 
Subscribed to by: client
Publisher: ESP32

Topic: [bioreactor_group_3/set_points] 
Subscribed to by: ESP32
Publisher: client

Payload: ```json
{
    "temperature_C": 32.0,
    "pH": 6.5,
    "rpm": 850.0
} ```
