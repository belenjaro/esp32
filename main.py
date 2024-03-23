# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

# This demo publishes to topic "result" and also subscribes to that topic.
# This demonstrates bidirectional TLS communication.
# You can also run the following on a PC to verify:
# mosquitto_sub -h test.mosquitto.org -t result
# To get mosquitto_sub to use a secure connection use this, offered by @gmrza:
# mosquitto_sub -h <my local mosquitto server> -t result -u <username> -P <password> -p 8883

# Public brokers https://github.com/mqtt/mqtt.github.io/wiki/public_brokers

# red LED: ON == WiFi fail
# green LED heartbeat: demonstrates scheduler is running.

from mqtt_as import MQTTClient
from mqtt_local import config
import asyncio
#import uasyncio as asyncio
import dht, machine
import json
import ubinascii
import unique_id
from settings import BROKER
#temperatura
#humedad
#setpiont es flotante 
#periodo es flotante
#destello ON/OFF
#modo auto/manual
#rele ON/OFF

CLIENT_ID = ubinascii.hexlify(unique_id()).decode('utf-8')

parametros={
    'temperatura':0.0,
    'humedad':0.0,
    'setpoint':26.5,
    'periodo':10,
    'modo':'auto'
    }

#sensor
d = dht.DHT22(machine.Pin(25))

#led
led = machine.Pin(27, machine.Pin.OUT)
led.value(1)# activo en bajo
#el led inicialmente esta apagado

#rele pin 12
rele= machine.Pin(12, machine.Pin.OUT)
rele.value(1) #activo en bajo
#esta apagado

bandestello=False

def sub_cb(topic, msg, retained):
    #redibo y decodifico
    topicodeco=topic.decode()
    msgdeco=msg.decode()
    #muestro el potico y el mensaje
    print('Topic = {} -> Valor = {}'.format(topicodeco, msgdeco))
    #condiciones para los topicos 
    if topicodeco == 'setpoint':
        try:
            parametros['setpoint']=float(msgdeco)
        except OSError:
            print("ERROR, debe ser flotante")
    elif topicodeco == "periodo":
        try:
            parametros['periodo']=float(msgdeco)
        except OSError:
            print("ERROR, debe ser flotante")
    elif topicodeco =="destello" :
        bandestello= (msgdeco.upper() == 'ON')#asigna True a bandestello si se cumple esto
        if bandestello == True:
            print("Destello activado")
        else:
            print("Destello desactivado")
    elif topicodeco=="modo":
        banmodo= msgdeco.lower()
        if banmodo == "manual":
            parametros['modo']=banmodo
            print("Modo manual")
        elif banmodo == "auto":
            parametros['modo']=banmodo
            print("Modo automatico")
        else:
            print("Modo incorrecto debe ser manual/auto")
    elif topicodeco== "rele":
        banrele= msgdeco.upper()
        if parametros['modo']=="manual":
            if banrele == "ON":
                rele.value(0)
                print("Rele encendido")
            elif banrele == "OFF":
                rele.value(1)
                print("Rele apagado")
    else:
        print("No hay dicho topico")
    
async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe('setpoint', 1)
    await client.subscribe('periodo', 1)
    await client.subscribe('modo', 1)
    await client.subscribe('destello', 1)
    await client.subscribe('rele', 1)

#lectura de temperatura y humedad
async def monitoreo():
    while True:
        d.measure()
        parametros['temperatura']=d.temperature()
        parametros['humedad']=d.humidity()
        if parametros['modo']=="auto":
            if parametros['temperatura']>parametros['setpoint']:
                parametros['rele']='ON'
                rele.value(0)#enciende rele
            else:
                parametros['rele']='OFF'
                rele.value(1)#apaga rele
        await asyncio.sleep(5)

#destello del led
#destellará por unos segundos 
#cuando reciba la orden "destello" por mqtt.
async def destello():
    while True:
        if bandestello==True:
            led.value(0)
            await asyncio.sleep(0.2)
            led.value(1)
            await asyncio.sleep(0.2)
            led.value(0)
            await asyncio.sleep(0.2)
            led.value(1)
        await asyncio.sleep(1)

async def main(client):
    await client.connect()
    await asyncio.sleep(2)  # Give broker time
    while True:
        try:
            await client.publish(f"iot/{CLIENT_ID}", json.dumps(parametros),qos=1)
        except OSError:
            print("Fallo del sensor")
        await asyncio.sleep(parametros['periodo'])  # Broker is slow
        
# Define configuration
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True


# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()


#await asyncio.gather(destello(),monitoreo(),conn_han(),wifi_han())
#await asyncio.create_task(destello(),monitoreo(),conn_han(),wifi_han())
#
