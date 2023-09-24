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

async def websocket_controls( websocket):
    print(f"Controls Running")
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
            break
        except Exception as e:
            # Handle other exceptions not specifically caught above
            print(f"An exception occurred: {str(e)}")

async def websocket_states( websocket):
    print(f"States Running")
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
            await asyncio.sleep(0.2)
        except websockets.ConnectionClosed:
            print("WebSocket connection closed.")
            break
        except Exception as e:
            # Handle other exceptions not specifically caught above
            print(f"An exception occurred: {str(e)}")

async def websocket_listener():
    uri = "wss://0w6s2vuxge.execute-api.ap-southeast-1.amazonaws.com/production"  # Replace with the WebSocket URL you want to connect to

    async with websockets.connect(ssl=ssl.SSLContext(ssl.PROTOCOL_TLS),
                                  extra_headers=headers,
                                  origin="*",
                                  uri = uri) as websocket:
        
        say_text('Control Script Connected')
        print('Connected to ' + uri)

        await asyncio.gather(websocket_controls( websocket), websocket_states( websocket))

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

def run_event_loop():
    try:
        print('asyncio.get_event_loop()')
        asyncio.get_event_loop().run_until_complete(websocket_listener())
    except Exception as e:
        # Handle other exceptions not specifically caught above
        print(f"An exception occurred: {str(e)}")
        tts_robot.say( str(e))
    finally:
        run_event_loop()

def startup_action():
    tts_robot.say( 'Controls waking up!')
    px.set_camera_tilt_angle( 45)
    time.sleep( 0.5)
    px.set_camera_tilt_angle( 0)

def closing_action():
    print('----------Controls.PY Stopping-----------------')
    px.stop()
    px.set_dir_servo_angle( -30)
    px.set_dir_servo_angle( 30)
    px.set_dir_servo_angle( 0)
    tts_robot.say( 'Controls Stopping')


if __name__ == "__main__":
    startup_action()
    run_event_loop()
    closing_action()

