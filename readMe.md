uses flask-mqtt
receive summary data (since this is what's provided by the simulator) and esp32 should collect this data every second and publish it via mqtt.
A new mqtt topic has to exist for communicating desired set points.
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
