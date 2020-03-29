import base64
import threading
import logging
from io import BytesIO

from .keyboard import Keyboard
from .music import parse_midi, autofit, consolidate
from .music_puncher import MusicPuncher
from flask import Flask, redirect, request, jsonify

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

instance = None


@app.route('/')
def hello_world():
    return redirect('/static/index.html')


@app.route('/api/punch', methods=['POST'])
def punch():
    if instance.puncher.active:
        raise RuntimeError("Puncher is still active!")

    content = request.json
    midiBase64 = content['midiFile']
    midiBytes = base64.b64decode(midiBase64)
    print(f"Received {len(midiBytes)} bytes")

    file = BytesIO(midiBytes)
    notes = parse_midi(file=file)
    notes = autofit(notes, instance.keyboard, 0)
    notes = consolidate(notes)

    x = threading.Thread(target=punch_function, args=[notes], daemon=True)
    x.start()

    return "ok"


@app.route('/api/stop', methods=['POST'])
def stop():
    instance.puncher.stop()
    return "ok"

def punch_function(notes):
    instance.puncher.run(notes)


@app.route('/api/status')
def status():
    return jsonify(instance.puncher.status())


class WebServer(object):

    def __init__(self, keyboard: Keyboard, puncher: MusicPuncher):
        self.keyboard = keyboard
        self.puncher = puncher
        global instance
        instance = self

    def run(self):
        app.run()
