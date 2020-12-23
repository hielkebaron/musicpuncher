import base64
import threading
from io import BytesIO

from flask import Flask, redirect, request, jsonify
from waitress import serve

from .keyboard import Keyboard, TransposeError
from .music import parse_midi, autofit, consolidate, write_midi, autotranspose, apply_transposition, get_notes
from .music_puncher import MusicPuncher

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

    instance.puncher.clearError()
    content = request.json
    instance.currentFile = content['filename']
    midiBase64 = content['midiFile']
    doAutotranspose = content['autotranspose']
    transposition = content['transpose']
    doAutofit = content['autofit']
    test = request.args.get('test') == 'true'

    midiBytes = base64.b64decode(midiBase64)

    file = BytesIO(midiBytes)
    notes = parse_midi(file=file)

    if doAutotranspose:
        try:
            notes = autotranspose(notes, instance.keyboard, best_effort=doAutofit)
        except TransposeError as error:
            return str(error), 400
    else:
        notes = apply_transposition(notes, transposition)

    if doAutofit:
        notes = autofit(notes, instance.keyboard)
    elif not instance.keyboard.does_fit(get_notes(notes)):
        return str('Notes do not fit on the keyboard, try autofit'), 400

    notes = consolidate(notes)


    if test:
        outfile = BytesIO()
        write_midi(notes, file=outfile)
        outBase64 = base64.b64encode(outfile.getbuffer())
        return outBase64
    else:
        x = threading.Thread(target=punch_function, args=[notes], daemon=True)
        x.start()
        return "ok"


@app.route('/api/stop', methods=['POST'])
def stop():
    print("Stop command received")
    instance.puncher.stop()
    return "ok"


def punch_function(notes):
    instance.puncher.run(notes)


@app.route('/api/status')
def status():
    status = instance.puncher.status()
    if status['active']:
        status['file'] = instance.currentFile
    return jsonify(status)


class WebServer(object):

    def __init__(self, keyboard: Keyboard, puncher: MusicPuncher, config):
        self.keyboard = keyboard
        self.puncher = puncher
        self.config = config
        global instance
        instance = self

    def run(self):
        serve(app, host=self.config['host'], port=self.config['port'])
