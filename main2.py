"""
#https://pasionelectronica.com/esp32-caracteristicas-y-pines/
#sensor
#d = dht.DHT22(machine.Pin(25))

#rele1 ventilador1
rele1= machine.Pin(9, machine.Pin.OUT)
rele1.value(1) #activo en bajo
#esta apagado

#rele2 ventilador2
rele2= machine.Pin(10, machine.Pin.OUT)
rele2.value(1) #activo en bajo

#modificacion de parametros
def sub_cb(topic, msg, retained):
    #redibo y decodifico
    topicodeco=topic.decode()
    msgdeco=msg.decode()
    global bandestello
    cambio=False    
    #muestro el topico y el mensaje
    print('Topic = {} -> Valor = {}'.format(topicodeco, msgdeco))
    #condiciones para los topicos 
    if topicodeco == 'setpoint1':
        try:
            parametros['setpoint1']=float(msgdeco)
            cambio=True
        except OSError:
            print("ERROR, debe ser flotante")
    elif topicodeco == 'setpoint2':
        try:
            parametros['setpoint2']=float(msgdeco)
            cambio=True
        except OSError:
            print("ERROR, debe ser flotante")
    elif topicodeco=="modo1":
        banmodo= msgdeco.lower()
        if banmodo == "manual":
            parametros['modo1']=banmodo
            cambio=True
            print("Modo manual")
        elif banmodo == "auto":
            parametros['modo1']=banmodo
            print("Modo automatico")
            cambio=True
        else:
            print("Modo incorrecto debe ser manual/auto")
    elif topicodeco == "modo2":
        banmodo = msgdeco.lower()
        if banmodo == "manual":
            parametros['modo2']=banmodo
            cambio=True
            print("Modo manual")
        elif banmodo == "auto":
            parametros['modo2']=banmodo
            print("Modo automatico")
            cambio=True
        else:
            print("Modo incorrecto debe ser manual/auto")
    elif topicodeco== "rele1":
        banrele= msgdeco.upper()
        if parametros['modo1']=="manual":
            if banrele == "ON":
                rele1.value(0)
                print("Rele encendido")
            elif banrele == "OFF":
                rele1.value(1)
                print("Rele apagado")
    elif topicodeco== "rele2":
        banrele= msgdeco.upper()
        if parametros['modo2']=="manual":
            if banrele == "ON":
                rele2.value(0)
                print("Rele encendido")
            elif banrele == "OFF":
                rele2.value(1)
                print("Rele apagado")
    elif topicodeco == "periodo":
        try:
            parametros['periodo']=float(msgdeco)
            cambio=True
        except OSError:
            print("ERROR, debe ser flotante")
    else:
        print("No hay dicho topico")
    
    if cambio is True:
        escribir_db()
async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(2)

#subcripcion a los topicos 
async def conn_han(client):
    await client.subscribe('setpoint1', 1)
    await client.subscribe('modo1', 1)
    await client.subscribe('rele1', 1)
    await client.subscribe('setpoint2', 1)
    await client.subscribe('modo2', 1)
    await client.subscribe('rele2', 1)
    await client.subscribe('periodo', 1)


#lectura de temperatura
async def monitoreo():
    while True:
        #d.measure()
        #parametros['temperatura']=d.temperature()
        if parametros['modo1']=="auto":
            if parametros['temperatura']>parametros['setpoint1']:
                parametros['rele1']='ON'
                rele1.value(0)#enciende rele
            else:
                parametros['rele1']='OFF'
                rele1.value(1)#apaga rele
        if parametros['modo2']=="auto":
            if parametros['temperatura']>parametros['setpoint2']:
                parametros['rele2']='ON'
                rele2.value(0)#enciende rele
            else:
                parametros['rele2']='OFF'
                rele2.value(1)#apaga rele       
        await asyncio.sleep(60)
  
async def main(client):
    await client.connect()
    await asyncio.sleep(4)  # Esperar para dar tiempo al broker
    while True:
        try:
            await client.publish(f"hector/{CLIENT_ID}", json.dumps(parametros), qos=1)
        except OSError as e:
            print(f"Fallo al publicar: {e}")
        await asyncio.sleep(parametros['periodo'])  # Esperar según el periodo definido
  
async def task(client):
    # Ejecutar monitoreo()y main() en paralelo
    await asyncio.gather(main(client),monitoreo())

def escribir_db():
    with open("db", "w+b") as f:
        db = btree.open(f)
        db[b'periodo'] = b"{}".format(str(parametros['periodo']))
        db[b'setpoint1'] = b"{}".format(str(parametros['setpoint1']))
        db[b'modo1'] = b"{}".format(str(parametros['modo1']))
        db[b'setpoint2'] = b"{}".format(str(parametros['setpoint2']))
        db[b'modo2'] = b"{}".format(str(parametros['modo2']))        
        db.flush()
        db.close()
    
def leer_db():
    with open("db", "r+b") as f:
        db = btree.open(f)
        parametros['periodo']=float(db[b'periodo'].decode())
        parametros['setpoint1']=float(db[b'setpoint1'].decode())
        parametros['modo1']=db[b'modo1'].decode()
        parametros['setpoint2']=float(db[b'setpoint2'].decode())
        parametros['modo2']=db[b'modo2'].decode()
        db.flush()
        db.close()

# Define configuration
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True

if 'db' not in os.listdir():
    print("Creando base de datos...")
    escribir_db()
else:
    print("Leyendo base de datos...")
    leer_db()
# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)
try:
    asyncio.run(task(client))
finally:
    client.close()
    asyncio.new_event_loop()
"""
