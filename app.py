#!/usr/bin/env python
from time import sleep

from flask import Flask, jsonify
import eiscp

app = Flask(__name__)
app.debug = True
receiver_address = '192.168.0.162'
SOURCE_TV = 'cd,tv/cd'

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/onkyo/status', methods=['GET'])
def get_status():
    receiver = eiscp.eISCP(receiver_address)
    main_power_result = receiver.command('main.power=query')
    main_power_status = main_power_result[1]
    if isinstance(main_power_status, tuple): # main power gives standby,off
        main_power_status = main_power_status[0]
    main_volume = receiver.command('main.volume=query')[1]
    main_source = receiver.command('main.source=query')[1]
    if isinstance(main_source, tuple):
        main_source = ','.join(main_source)

    receiver.disconnect()

    return jsonify(
    {
      "status": {
        "main": {
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
    receiver.command(zone + '.power=' + status)
    receiver.disconnect()
    return get_status()

@app.route('/onkyo/<string:zone>/volume/<int:level>', methods=['POST'])
def set_volume(zone, level):
    if zone != 'main' and zone != 'zone2':
        return 'unknown zone', 400
    if level < 0: level = 0
    if level > 100: level = 100

    receiver = eiscp.eISCP(receiver_address)
    receiver.command(zone + '.volume=' + str(level))
    receiver.disconnect()

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

app.run(host='0.0.0.0', port=8080)
#!/usr/bin/env python

from flask import Flask, jsonify
import eiscp

app = Flask(__name__)
app.debug = True
receiver_address = '192.168.86.27'
SOURCE_TV = 'cd,tv/cd'
SOURCE_APPLETV = 'video2,cbl,sat'

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/onkyo/status', methods=['GET'])
def get_status():
    receiver = eiscp.eISCP(receiver_address)
    main_power_result = receiver.command('main.power=query')
    main_power_status = main_power_result[1]
    if isinstance(main_power_status, tuple): # main power gives standby,off
        main_power_status = main_power_status[0]
    main_volume = receiver.command('main.volume=query')[1]
    main_source = receiver.command('main.source=query')[1]
    if isinstance(main_source, tuple):
        main_source = ','.join(main_source)

    zone2_power_result = receiver.command('zone2.power=query')
    zone2_power_status = zone2_power_result[1]
    zone2_volume = receiver.command('zone2.volume=query')[1]
    zone2_source = receiver.command('zone2.selector=query')[1]
    if isinstance(zone2_source, tuple):
        zone2_source = ','.join(zone2_source)

    receiver.disconnect()

    return jsonify(
    {
      "status": {
        "main": {
            "status": main_power_status,
            "volume": volume_output(main_volume),
            "source": source_output(main_source)
        },
        "zone2": {
            "status": zone2_power_status,
            "volume": volume_output(zone2_volume),
            "source": source_output(zone2_source)
        }
      }
    })

@app.route('/onkyo/<string:zone>/power/<string:status>', methods=['PUT'])
def set_power(zone, status):
    if zone != 'main' and zone != 'zone2':
        return 'unknown zone', 400
    if status != 'on' and status != 'standby':
        return 'unknown status', 400
    receiver = eiscp.eISCP(receiver_address)
    receiver.command(zone + '.power=' + status)
    receiver.disconnect()
    return get_status()

@app.route('/onkyo/<string:zone>/volume/<int:level>', methods=['PUT'])
def set_volume(zone, level):
    if zone != 'main' and zone != 'zone2':
        return 'unknown zone', 400
    if level < 0: level = 0
    if level > 80: level = 80

    receiver = eiscp.eISCP(receiver_address)
    receiver.command(zone + '.volume=' + str(level))
    receiver.disconnect()

    return jsonify(
    {
        "zone": zone,
        "volume": level
    })

def volume_output(volume):
    return volume if volume != 'N/A' else 0

def source_output(source):
    if source == SOURCE_TV:
        return 'tv'
    elif source == SOURCE_APPLETV:
        return 'appletv'
    else:
        return source

app.run(host='0.0.0.0', port=8080)
