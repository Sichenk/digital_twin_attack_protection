import subprocess
import time
import json
import statistics
import os
RESULTS_FILE = "benchmark_rtt_results.json"
def run_scenario(name, broker, port, use_tls, ca_cert="ca.crt", duration=60):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"  {broker}:{port}, TLS={use_tls}")
    print(f"{'='*60}")
    cmd = [
        "python3", "sensor_with_tls_benchmark.py",
        "--broker", broker,
        "--port", str(port),
        "--duration", str(duration),
        "--messages", "100"
    ]
    if use_tls:
        cmd.append("--tls")
        cmd.append("--ca-cert")
        cmd.append(ca_cert)
    
    print(f"[RUNNING] {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    last_result = {}
    for line in process.stdout:
        print(f"  {line.strip()}")
        
        if "Final result:" in line:
            import ast
            try:
                result_str = line.split("Final result: ")[1]
                last_result = ast.literal_eval(result_str)
            except:
                pass
    process.wait()
    return last_result
def main():
    BROKER = "192.168.0.156"
    BROKER_MITM = "192.168.0.192"
    CA_CERT = "ca.crt"
    DURATION = 1000
    scenarios = [
        {
            "name": "1. Без защиты (прямое подключение, без TLS)",
            "broker": BROKER,
            "port": 1883,
            "use_tls": False
        },
        {
            "name": "2. Через MITM-прокси (без TLS)",
            "broker": BROKER_MITM,
            "port": 1884,
            "use_tls": False
        },
        {
            "name": "3. TLS-защита (прямое подключение)",
            "broker": BROKER,
            "port": 8883,
            "use_tls": True
        },
        {
            "name": "4. TLS через MITM-прокси",
            "broker": BROKER_MITM,
            "port": 1885,
            "use_tls": True
        }
    ]
    results = []
    for scenario in scenarios:
        if scenario["use_tls"] and not os.path.exists(CA_CERT):
            print(f"\nTLS certificate {CA_CERT} not found, skipping {scenario['name']}")
            continue
        
        stats = run_scenario(
            name=scenario["name"],
            broker=scenario["broker"],
            port=scenario["port"],
            use_tls=scenario["use_tls"],
            ca_cert=CA_CERT,
            duration=DURATION
        )
        stats["scenario"] = scenario["name"]
        results.append(stats)
        time.sleep(2)
    # Сохранение результатов
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    # Вывод сводной таблицы
    print("\n" + "="*90)
    print("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ RTT")
    print("="*90)
    print(f"{'Сценарий':<45} {'Подтверждено':<12} {'Среднее RTT (мс)':<18} {'Потери %':<10}")
    print("-"*85)
    for r in results:
        if "error" in r:
            print(f"{r['scenario']:<45} {'ОШИБКА':<12} {'ОШИБКА':<18} {'N/A':<10}")
        else:
            print(f"{r['scenario']:<45} {r.get('confirmed', 0):<12} {r.get('mean_ms', 0):<18.2f} {r.get('loss_percent', 0):<10.1f}")
    print("="*90)
if __name__ == "__main__":
    main()
