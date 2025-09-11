import time
import paho.mqtt.client as mqtt

# ==== MQTT Konfiguration ====
BROKER = "87.106.168.214"      # Hostname/IP deines MQTT Brokers
PORT = 1883               # Standard-Port für MQTT
USERNAME = "casiot"           # falls nötig
PASSWORD = "casiot25"           # falls nötig

# ==== Topics ====
TOPIC_TEMP = "raspi_tft_v2/ist"
TOPIC_HUM = "raspi_tft_v2/hum"
TOPIC_CONTROL = "climate/coil/set"

# ==== Startwerte ====
temperature = 22.0
humidity = 50.0
mode = 0   # 0 = idle, 1 = heat, -1 = cool

# ==== Grenzen ====
TEMP_MIN, TEMP_MAX = 15.0, 30.0
HUM_MIN, HUM_MAX = 30.0, 80.0


# ==== Callback für eingehende Nachrichten ====
def on_message(client, userdata, msg):
    global mode
    try:
        payload = msg.payload.decode().strip()
        if payload in ["-1", "0", "1"]:
            mode = int(payload)
            print(f"[MQTT] Mode geändert: {mode}")
        else:
            print(f"[WARN] Ungültige Nachricht: {payload}")
    except Exception as e:
        print(f"[ERROR] on_message: {e}")


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def main():
    global temperature, humidity, mode

    client = mqtt.Client()
    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)

    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Auf Steuer-Topic hören
    client.subscribe(TOPIC_CONTROL)

    client.loop_start()

    print("[INFO] Simulation gestartet...")

    try:
        while True:
            # Temperatur/Humidity verändern je nach Modus
            if mode == 1:  # Heizen
                temperature += 1.0
                humidity -= 1.0
            elif mode == -1:  # Kühlen
                temperature -= 1.0
                humidity += 1.0
            # Idle = keine Veränderung

            # Clamp auf definierte Grenzen
            temperature = clamp(temperature, TEMP_MIN, TEMP_MAX)
            humidity = clamp(humidity, HUM_MIN, HUM_MAX)

            # Werte publishen
            client.publish(TOPIC_TEMP, f"{temperature:.1f}")
            client.publish(TOPIC_HUM, f"{humidity:.1f}")

            print(f"[PUB] Temp={temperature:.1f}°C, Hum={humidity:.1f}% (Mode={mode})")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Simulation beendet.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()