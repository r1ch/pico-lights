import CONFIG
import json
import time
import network
import plasma
from plasma import plasma_stick
from umqtt.simple import MQTTClient

NUM_LEDS = 50

# WS2812 / NeoPixel™ LEDs
led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma_stick.DAT, color_order=plasma.COLOR_ORDER_RGB)

# Start updating the LED strip
led_strip.start()
led_strip.set_rgb(0,0,255,0)

h = 0.0
s = 0.0
brightness = 0
state = "OFF"
effect = False

rainbow = [320,280,240,120,60,30,0]
readingFrom = 0
readingTo = 6

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(CONFIG.SSID, CONFIG.PSK)
led_strip.set_rgb(1,0,255,0)
led_strip.set_rgb(5,255,255,0)
while wlan.isconnected() == False:
    led_strip.set_rgb(5,0,255,0)
    print('Waiting for connection...')
    time.sleep(1)
    led_strip.set_rgb(5,255,255,0)
    time.sleep(1)
print("Connected to WiFi")
led_strip.set_rgb(2,0,255,0)



def publish_state():
    global h,s,brightness,state,effect
    x = {
        'state': state,
        'brightness': brightness,
        'color': {
            'h': h,
            's': s,
        },
        'effect': effect
    }
    mqtt_client.publish(CONFIG.MQTT_STATUS_TOPIC,json.dumps(x))

def process_msg(topic, msg):
    global h,s,brightness,state,effect
    j = json.loads(msg)
    if "color" in j:
        if effect != "Reading": effect = False
        if "h" in j["color"] : h = j["color"]["h"]
        if "s" in j["color"] : s = j["color"]["s"]
    if "brightness" in j : brightness = j["brightness"]
    if "state" in j : state = j["state"]
    if "effect" in j : effect = j["effect"] 
    set_state()

def set_state():
    global h,s,brightness,state,effect,rainbow,readingFrom,readingTo
    if effect == "Rainbow":
        for i in range(NUM_LEDS):
            led_strip.set_hsv(i,rainbow[i%len(rainbow)]/360,1.0,brightness/255*int(state=="ON"))
    elif effect == "Reading":
        for i in range(NUM_LEDS):
            led_strip.set_hsv(i,h/360,s/100,brightness/255*int(state=="ON")*int(i>=readingFrom and i<=readingTo))
    else:
        for i in range(NUM_LEDS):
            led_strip.set_hsv(i,h/360,s/100,brightness/255*int(state=="ON"))
    publish_state()


# Initialize our MQTTClient and connect to the MQTT server
mqtt_client = MQTTClient(
        client_id=CONFIG.MQTT_ID,
        server=CONFIG.MQTT_HOST,
        user=CONFIG.MQTT_USERNAME,
        password=CONFIG.MQTT_PASSWORD)

mqtt_client.connect()
led_strip.set_rgb(3,0,255,0)
mqtt_client.set_callback(process_msg)
mqtt_client.subscribe(CONFIG.MQTT_SET_TOPIC)
print("Connected to MQTT")
led_strip.set_rgb(4,0,255,0)
set_state()

while True:
    mqtt_client.wait_msg()
