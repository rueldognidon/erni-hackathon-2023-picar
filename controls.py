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
                message = await websocket.recv()
                print(f"Received: {message}")
                command = json.loads(message)
                with px_lock:
                    operation = command['operation']

                    if  operation == 'set_speed':
                        cmd_set_speed( command)
                    elif operation == 'stop':
                        cmd_stop( command)
                    elif operation == 'set_direction':
                        cmd_set_direction( command)
                    elif operation == 'set_head_rotate':
                        cmd_set_head_rotate( command)
                    elif operation == 'set_head_tilt':
                        cmd_set_head_tilt( command)
                    elif operation == 'say':
                        cmd_say( command)
                    else:
                        print('Unknown command')
            except websockets.ConnectionClosed:
                print("WebSocket connection closed.")
                say_text('Disconnected!')
                say_text('Disconnected!')
                say_text('Disconnected!')
                break
            except Exception as e:
                # Handle other exceptions not specifically caught above
                print(f"An exception occurred: {str(e)}")
        
        asyncio.get_event_loop().run_until_complete(websocket_listener())

def cmd_say( command):
    text = command['text']

    tts_robot.say( text)

def say_text( text):
    tts_robot.say( text)


def cmd_set_head_tilt( cmd):
    angle = cmd['angle']

    if( -45 < angle & angle < 45):
        px.set_camera_tilt_angle( angle)

def cmd_set_head_rotate( cmd):
    angle = cmd['angle']

    if( -45 < angle & angle < 45):
        px.set_cam_pan_angle( angle)

def cmd_set_speed( cmd):
    speed = cmd['speed']

    if( speed > 0 & speed < 50):
        px.forward( speed)
    elif( speed < 0 & speed > -50):
        px.backward( -speed)
    else:
        px.stop()

def cmd_stop( cmd):
    px.stop()

def cmd_set_direction( cmd):
    angle = cmd['angle']

    if( -45 < angle & angle < 45):
        px.set_dir_servo_angle( angle)


if __name__ == "__main__":
    print('asyncio.get_event_loop()')
    asyncio.get_event_loop().run_until_complete(websocket_listener())
    print('----------Controls.PY Stopping-----------------')
    px.stop()
    tts_robot.say( 'Controls Stopping')
