// import mqtt from "mqtt";

const url = "mqtt://engf0001.cs.ucl.ac.uk:1883/mqtt";
const topic = "bioreactor_sim/singlefaults/telemetry/summary";
// Connect
const client = mqtt.connect(url, (options = {}));
// Subscribe to normal data streams

client.on("connect", () => {
  console.log("Connected to broker");
  client.subscribe(topic, (err) => {
    console.log("Subscribed to topic");
  });
});

// Receiving
client.on("message", (topic, message) => {
  console.log(message.toString());
  // client.end
});
