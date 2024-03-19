import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('conectando a la red...')
    wlan.connect('SalaTI', 'edupublica')
    while not wlan.isconnected():
        pass
