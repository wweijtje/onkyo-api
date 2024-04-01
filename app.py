#!/usr/bin/env python
from time import sleep

from flask import Flask, jsonify
import eiscp

app = Flask(__name__)
app.debug = False
receiver_address = '192.168.0.162'
SOURCE_TV = 'cd,tv/cd'

@app.route('/')
def index():
    return f"Onkyo API says hello!  Receiver at {receiver_address}"

def _get_power_status(receiver:eiscp.eISCP,zone='main'):
    """
    Collects the power status

    :param receiver: receiver object
    :param zone: default 'main'
    :return:
    """
    power_result = receiver.command(f'{zone}.power=query')
    power_status = power_result[1]
    if isinstance(power_status, tuple): # main power gives standby,off
        power_status = power_status[0]

    return power_status

@app.route('/onkyo/discover', methods=['POST'])
def discover():
    # Forces to search for the receiver_address
    global receiver_address
    receivers = eiscp.eISCP.discover(timeout=5)
    print('test')
    print(receivers)
    receivers_output = []
    for r in receivers:
        receivers_output.append(
            {
                'device':r.info['model_name'],
                'host':r.host,
                'port':r.port
            }
        )
    receiver_address = receivers_output[0]['host']
    return jsonify(receivers_output)



@app.route('/onkyo/<string:zone>/status', methods=['GET'])
def get_status(zone):
    with eiscp.eISCP(receiver_address) as receiver:
        main_power_status = _get_power_status(receiver, zone=zone)

        main_volume = receiver.command(f'{zone}.volume=query')[1]
        main_source = receiver.command(f'{zone}.source=query')[1]
        if isinstance(main_source, tuple):
            main_source = ','.join(main_source)

    return jsonify(
    {
      "status": {
        f"{zone}": {
            "status": main_power_status,
            "volume": volume_output(main_volume),
            "source": source_output(main_source)
        }
      }
    })

@app.route('/onkyo/<string:zone>/power/<string:status>', methods=['POST'])
def set_power(zone, status):
    if zone != 'main' and zone != 'zone2':
        return 'unknown zone', 400
    if status != 'on' and status != 'standby':
        return 'unknown status', 400
    print(f'Received {zone}.power={status}')
    receiver = eiscp.eISCP(receiver_address)
    receiver.command(f'{zone}.power={status}')
    receiver.disconnect()
    return get_status(zone)

@app.route('/onkyo/<string:zone>/volume/<int:level>', methods=['POST'])
def set_volume(zone, level):
    if zone != 'main' and zone != 'zone2':
        return 'unknown zone', 400
    if level < 0: level = 0
    if level > 100: level = 100

    with eiscp.eISCP(receiver_address) as receiver:
        receiver.command(zone + '.volume=' + str(level))

    return jsonify(
    {
        "zone": zone,
        "volume": level
    })

@app.route('/onkyo/<string:zone>/tunein/<int:preset>', methods=['POST'])
def set_tunein_preset(zone, preset):
    """
    Moves through the menu and activates the tunein preset

    Assumes the device is already on.

    :param zone:
    :param preset:
    :return:
    """
    if zone != 'main':
        return 'unknown zone', 400

    with eiscp.eISCP(receiver_address) as receiver:
        # Check if the power is on, if not turn on the device
        status = _get_power_status(receiver, zone=zone)
        if status == 'standby':
            # Turn device on and wait a bit
            receiver.command(zone + '.power=on')
            sleep(3)

        receiver.command(f'{zone}.volume=80') # Sets a default volume
        _ = receiver.raw("SLI2B") # Set to NET

        receiver.send("NSV0E0") # Set to Tunein
        sleep(3)
        print("NLSI00001")
        resp = receiver.raw("NLSI00001") # My presets
        sleep(3)
        print(f"{resp}:NLSI{preset:05}")
        _ = receiver.raw(f"NLSI{preset:05}") # Set preset

    return jsonify(
    {
        "zone": zone,
        "preset": preset
    })


def volume_output(volume):
    return volume if volume != 'N/A' else 0

def source_output(source):
    if source == SOURCE_TV:
        return 'tv'
    else:
        return source

