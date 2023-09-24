import asyncio
import websockets
import ssl
from picarx import Picarx
from robot_hat import TTS
import time
import json
from threading import Lock

headers= {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'Upgrade',
        'Host': ...,
        'Origin': ...,
        'Pragma': 'no-cache',
        'Upgrade': 'websocket',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'
    }

px = Picarx()
px_lock = Lock()
tts_robot = TTS()
# Vilib.camera_start(vflip=False,hflip=False)
# Vilib.display(local=False,web=True)

# client.connect("localhost", 1883, 60)

async def websocket_listener():
    uri = "wss://0w6s2vuxge.execute-api.ap-southeast-1.amazonaws.com/production"  # Replace with the WebSocket URL you want to connect to

    async with websockets.connect(ssl=ssl.SSLContext(ssl.PROTOCOL_TLS),
                                  extra_headers=headers,
                                  origin="*",
                                  uri = uri) as websocket:
        say_text('Control Script Connected')
        print('Connected to ' + uri)

        while True:
            try:
                with px_lock:
                    distance = round( px.ultrasonic.read(), 2)
                    grayscale = px.get_grayscale_data()

                event = {
                    "distance" : distance,
                    "grayscale" : grayscale
                }
                
                payload = {
                    "action" : "sendToRemoteController",
                    "command" : json.dumps( event)
                }
                
                print(f"Sending: {json.dumps( payload)}")
                await websocket.send(json.dumps( payload))

                # client2.publish( "state", json.dumps( event))

                time.sleep( 0.2)
            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
                say_text('Disconnected!')
                say_text('Disconnected!')
                say_text('Disconnected!')
                break
            except Exception as e:
                # Handle other exceptions not specifically caught above
                print(f"An exception occurred: {str(e)}")

def cmd_say( command):
    text = command['text']

    tts_robot.say( text)

def say_text( text):
    tts_robot.say( text)


def run_event_loop():
    try:
        print('asyncio.get_event_loop()')
        asyncio.get_event_loop().run_until_complete(websocket_listener())
    except Exception as e:
        # Handle other exceptions not specifically caught above
        print(f"An exception occurred: {str(e)}")
        tts_robot.say( str(e))
    #finally:
        #run_event_loop()

def startup_action():
    tts_robot.say( 'States waking up!')

def closing_action():
    print('----------States.PY Stopping-----------------')
    tts_robot.say( 'States Stopping')


if __name__ == "__main__":
    startup_action()
    run_event_loop()
    closing_action()