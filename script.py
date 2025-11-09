import pygame
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import json
import time

# Configuracion MQTT
BROKER = "localhost"
PORT = 1883
TOPIC_CONTROL = "robot/control"

connected = False

def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    if reason_code == 0:
        print("Conectado al broker MQTT")
        connected = True
    else:
        print(f"Error de conexión: {reason_code}")
        connected = False


def on_disconnect(client, userdata, flags, reason_code, properties):
    global connected
    print(f"Desconectado del broker (reason: {reason_code})")
    connected = False


def on_publish(client, userdata, mid, reason_code, properties):
    pass


client = mqtt.Client(
    client_id="JoystickPublisher",
    callback_api_version=CallbackAPIVersion.VERSION2
)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    # Esperar a que se conecte
    timeout = 5
    start = time.time()
    while not connected and (time.time() - start) < timeout:
        time.sleep(0.1)

    if not connected:
        print(f"❌ No se pudo conectar al broker en {timeout} segundos")
        exit()

except Exception as e:
    print("No se pudo conectar al broker MQTT:", e)
    exit(1)

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No se detecto ningun joystick")
    exit(1)
    # Se podria probar con el teclado

else:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Joystick detectado: ", joystick.get_name())
    # USE_KEYBOARD = False

print(f"📡 Broker: {BROKER}:{PORT}")
print(f"📤 Topic: {TOPIC_CONTROL}")

THRESHOLD = 0.3

def get_joystick_input(x, y):
    y = -y

    if abs(x) < THRESHOLD and abs(y) < THRESHOLD:
        return "PARAR"
    
    if abs(y) > abs(x):
        return "ADELANTE" if y > THRESHOLD else "ATRAS"
    else:
        return "DERECHA" if x > THRESHOLD else "IZQUIERDA"
    

# def get_keyboard_input():

last_command = None

try:
    clock = pygame.time.Clock()
    screen = None

    running = True
    while True:
        if not connected:
            print("⚠️  Reconectando...")
            try:
                client.reconnect()
            except:
                pass
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                raise KeyboardInterrupt
            
        pygame.event.pump()
        x_axis = joystick.get_axis(0)
        y_axis = joystick.get_axis(1)
        command = get_joystick_input(x_axis, y_axis)

        if command and command != last_command:
            payload = {
                "comando": command
            }

            result = client.publish(TOPIC_CONTROL, json.dumps(payload))

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Comando enviado: {command}")
                last_command = command
            else:
                print("Error al publicar el comando")
        clock.tick(20)

except KeyboardInterrupt:
    print("Saliendo...")
    client.publish(TOPIC_CONTROL, json.dumps({"comando": "PARAR"}))
finally:
    try:
        if connected:
            client.publish(TOPIC_CONTROL, json.dumps({"comando": "PARAR"}))
            time.sleep(0.1)
    except:
        pass

    pygame.quit()
    client.loop_stop()
    client.disconnect()
    print("Desconectado del broker MQTT")
    exit(0)
