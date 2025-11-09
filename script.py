import pygame
import paho.mqtt.client as mqtt
import json
import time

# Configuracion MQTT
BROKER = "localhost"
PORT = 1883
TOPIC_CONTROL = "robot/control"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado al broker MQTT")
    else:
        print("Fallo de conexion, codigo de resultado: ", rc)


def on_publish(client, userdata, mid):
    pass


client = mqtt.Client("JoystickPublisher")
client.on_connect = on_connect
client.on_publish = on_publish

try:
    client.connect(BROKER, PORT, 60)
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

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
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
    pygame.quit()
    client.loop_stop()
    client.disconnect()
    print("Desconectado del broker MQTT")
    exit(0)
