import random
import time
import json
import ssl
import argparse
import statistics
from paho.mqtt import client as mqtt_client
TOPIC = "sensors/temperature"
CA_CERT = "ca.crt"
all_rtts = []
sent_times = {}
def on_publish(client, userdata, mid, reason_code, properties):
    if mid in sent_times:
        rtt = (time.time() - sent_times[mid]) * 1000  # в миллисекундах
        all_rtts.append(rtt)
        print(f"[RTT] Message {mid} RTT: {rtt:.2f}ms")
        del sent_times[mid]
def connect_mqtt_normal(broker, port, client_id):
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"{client_id} connected to broker (plain TCP, port {port})")
        else:
            print(f"Failed to connect, return code {reason_code}")
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect(broker, port)
    return client
def connect_mqtt_tls(broker, port, client_id, ca_cert=CA_CERT):
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"{client_id} connected to broker (TLS, port {port})")
        else:
            print(f"Failed to connect, return code {reason_code}")
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id)
    client.on_connect = on_connect
    client.on_publish = on_publish
    try:
        client.tls_set(
            ca_certs=ca_cert,
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        client.tls_insecure_set(True)
    except Exception as e:
        print(f"TLS configuration error: {e}")
        raise
    client.connect(broker, port)
    return client
def run_benchmark(broker, port, use_tls=False, ca_cert=CA_CERT, duration=60, target_messages=30):
    global all_rtts, sent_times
    all_rtts = []
    sent_times = {}
    client_id = f"benchmark-{random.randint(1000, 9999)}"
    if use_tls:
        client = connect_mqtt_tls(broker, port, client_id, ca_cert)
    else:
        client = connect_mqtt_normal(broker, port, client_id)
    client.loop_start()
    time.sleep(2)
    start_time = time.time()
    sent_count = 0
    print(f"\n{'='*60}")
    print(f"Starting benchmark: {broker}:{port}, TLS={use_tls}")
    print(f"Duration: {duration}s, Target messages: {target_messages}")
    print(f"{'='*60}\n")
    try:
        temp = 20.0
        direction = 1
        while time.time() - start_time < duration and len(all_rtts) < target_messages:
            temp += random.uniform(-0.5, 0.5) * direction
            if temp > 35:
                direction = -1
            elif temp < 18:
                direction = 1
            payload = json.dumps({
                "sensor_id": client_id,
                "temperature": round(temp, 1),
                "timestamp": time.time(),
                "sequence": sent_count
            })
            result = client.publish(TOPIC, payload, qos=1)
            sent_times[result.mid] = time.time()
            sent_count += 1
            print(f"Sent message {sent_count}, mid={result.mid}, temp={round(temp, 1)}°C")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        time.sleep(3)
        client.loop_stop()
        client.disconnect()
    # Статистика
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Messages sent: {sent_count}")
    print(f"Messages confirmed (RTT measured): {len(all_rtts)}")
    if all_rtts:
        print(f"\nRTT Statistics (ms):")
        print(f"  Mean:   {statistics.mean(all_rtts):.2f} ms")
        print(f"  Median: {statistics.median(all_rtts):.2f} ms")
        print(f"  Min:    {min(all_rtts):.2f} ms")
        print(f"  Max:    {max(all_rtts):.2f} ms")
        if len(all_rtts) > 1:
            print(f"  Stdev:  {statistics.stdev(all_rtts):.2f} ms")
        print(f"  Loss:   {(1 - len(all_rtts)/sent_count)*100:.1f}%")
        return {
            "sent": sent_count,
            "confirmed": len(all_rtts),
            "mean_ms": statistics.mean(all_rtts),
            "median_ms": statistics.median(all_rtts),
            "min_ms": min(all_rtts),
            "max_ms": max(all_rtts),
            "stdev_ms": statistics.stdev(all_rtts) if len(all_rtts) > 1 else 0,
            "loss_percent": (1 - len(all_rtts)/sent_count)*100
        }
    else:
        print("\n[ERROR] No messages confirmed!")
        return {"error": "No messages confirmed"}
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", "-b", default="192.168.0.156")
    parser.add_argument("--port", "-p", type=int, default=1883)
    parser.add_argument("--tls", "-t", action="store_true")
    parser.add_argument("--ca-cert", "-c", default="ca.crt")
    parser.add_argument("--duration", "-d", type=int, default=60)
    parser.add_argument("--messages", "-m", type=int, default=30)
    args = parser.parse_args()
    result = run_benchmark(
        broker=args.broker,
        port=args.port,
        use_tls=args.tls,
        ca_cert=args.ca_cert,
        duration=args.duration,
        target_messages=args.messages
    )
    print(f"\nFinal result: {result}")
if __name__ == "__main__":
    main()
