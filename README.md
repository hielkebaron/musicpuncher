# musicpuncher
Software for a Music Box card puncher

## Development

```bash
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
```

Run the tests:

```bash
pytest
```

To mock the actual pi/pigpio library in the examples below, first run:
```commandline
export MOCK_PIGPIO=true
```

To process a midi file:
```commandline
python main.py <file.mid>
```

To start as a web server:
```commandline
python main.py --serve
```
and open [http://localhost:8080/](http://localhost:8080/) in your browser. Replace localhost with the hostname or ip of your pi if you run this command from a pi.