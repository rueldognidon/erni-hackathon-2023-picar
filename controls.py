import asyncio
import websockets
import ssl
from vilib import Vilib
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

current_state = None
px_power = 10
offset = 20
last_state = "stop"

px = Picarx()
px_lock = Lock()
tts_robot = TTS()
Vilib.camera_start(vflip=False,hflip=False)
Vilib.display(local=False,web=True)

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
                elif operation == 'auto':
                    auto( command)
                elif operation == 'path_finder':
                    pathfinder( command)
                elif operation == 'line_tracer':
                    lineTracing( command)
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

    say_text('Ze bluetooth je vice iz ready to pair')
    async with websockets.connect(ssl=ssl.SSLContext(ssl.PROTOCOL_TLS),
                                  extra_headers=headers,
                                  origin="*",
                                  uri = uri) as websocket:
        
        say_text('Web Socket Connected')
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

def forward( slp):
    px.set_dir_servo_angle( 0)
    px.forward( 10)
    time.sleep( slp)

def backward( slp):
    px.set_dir_servo_angle( 0)
    px.backward( 10)
    time.sleep( slp)

def forwardleft( slp):
    px.set_dir_servo_angle( -20)
    px.forward( 10)
    time.sleep( slp)

def backwardleft( slp):
    px.set_dir_servo_angle( -20)
    px.backward( 10)
    time.sleep( slp)

def forwardright( slp):
    px.set_dir_servo_angle( 20)
    px.forward( 10)
    time.sleep( slp)

def backwardright( slp):
    px.set_dir_servo_angle( 20)
    px.backward( 10)
    time.sleep( slp)

def stop():
    px.set_dir_servo_angle( 0)
    px.stop()

## Start of Line Tracing


def outHandle():
    global last_state, current_state
    if last_state == 'left':
        px.set_dir_servo_angle(-30)
        px.backward(10)
    elif last_state == 'right':
        px.set_dir_servo_angle(30)
        px.backward(10)
    while True:
        gm_val_list = px.get_grayscale_data()
        gm_state = get_status(gm_val_list)
        print("outHandle gm_val_list: %s, %s"%(gm_val_list, gm_state))
        currentSta = gm_state
        if currentSta != last_state:
            break
    time.sleep(0.001)

def get_status(val_list):
    _state = px.get_line_status(val_list)  # [bool, bool, bool], 0 means line, 1 means background
    print("")
    if _state == [0, 0, 0]:
        return 'stop'
    elif _state[1] == 1:
        return 'forward'
    elif _state[0] == 1:
        return 'right'
    elif _state[2] == 1:
        return 'left'
    
def lineTracing( cmd):
    try:
        while True:
            gm_val_list = px.get_grayscale_data()
            gm_state = get_status(gm_val_list)
            print("gm_val_list: %s, %s"%(gm_val_list, gm_state))
            print(gm_state[0], last_state)

            if gm_state != "stop":
                last_state = gm_state

            if gm_state == 'forward':
                px.set_dir_servo_angle(0)
                px.forward(px_power) 
            elif gm_state == 'left':
                px.set_dir_servo_angle(offset)
                px.forward(px_power) 
            elif gm_state == 'right':
                px.set_dir_servo_angle(-offset)
                px.forward(px_power) 
            else:
                outHandle()
    finally:
        px.stop()
        print("stop and exit")
        time.sleep(0.1)

# End of line tracing

def waitForWhite():
    ctr = 0
    while True:
        grayscale = px.get_grayscale_data()
        
        g1 = int(grayscale[0])
        g2 = int(grayscale[1])
        g3 = int(grayscale[2])

        print(f'g1:{str(g1)} g2:{str(g2)} g3:{str(g3)}')
        
        if((g1 > 60) and  (g2 > 60) and (g3 > 60)):
            print('white detected')
            break
        
        time.sleep( 0.1)
        ctr = ctr + 1
        if( ctr > 60 ):
            raise Exception("Wait for white timeout")

def forwardThenLeft():
    forward( 0.5)
    waitForWhite()
    forwardleft( 0.5)
    waitForWhite()


def forwardThenRight():
    forward( 0.5)
    waitForWhite()
    forwardright( 0.5)
    waitForWhite()

def pathfinder( cmd):
    try:
        forwardThenLeft()
        forwardThenRight()
        forwardThenRight()
        forwardThenLeft()
        forwardThenLeft()
        forwardThenLeft()
        forwardThenLeft()
        forwardThenRight()
        forwardThenRight()
        forwardThenLeft()
        stop()
    except:
        stop()



def auto( cmd):
    s1 = cmd['s1']
    s2 = cmd['s2']
    s3 = cmd['s3']
    s4 = cmd['s4']
    s5 = cmd['s5']
    s6 = cmd['s6']
    s7 = cmd['s7']
    s8 = cmd['s8']
    s9 = cmd['s9']
    s10 = cmd['s10']
    s11 = cmd['s11']
    s12 = cmd['s12']
    s13 = cmd['s13']

    forward( s1)
    forwardleft( s2)
    forward( s3)
    forwardright( s4)
    forward( s5)
    forwardleft( s6)
    forward( s7)
    forwardleft( s8)
    forward( s9)
    forwardleft( s10)
    forward( s11)
    forwardright( s12)
    forward( s13)
    stop()


def run_event_loop():
    try:
        print('asyncio.get_event_loop()')
        asyncio.get_event_loop().run_until_complete(websocket_listener())
    except Exception as e:
        # Handle other exceptions not specifically caught above
        print(f"An exception occurred: {str(e)}")
        tts_robot.say( 'Error Occured')
    # finally:
    #     run_event_loop()

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

