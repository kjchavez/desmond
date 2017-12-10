# Desmond Project

> See you in another life, brother.

```
protoc --python_out=./ desmond/**/*.proto
```

pip install https://github.com/zeromq/pyre/archive/master.zip

```
sqlite3 ~/.desmond/sensorlogs.db

select datetime(time_usec, 'unixepoch', 'localtime'), payload from sensordata;
```

The Jupyter notebook as a dashboard will get out of hand pretty quickly
unless we do something like http://pascalbugnion.net/blog/ipython-notebooks-and-git.html.

https://developers.google.com/protocol-buffers/docs/reference/python/google.protobuf.descriptor.Descriptor-class


## Hello World demo

In two terminals fire up:

```
python tools/stdout_actuator.py
```

and

```
python tools/commandline_text_sensor.py
```

This is meant to simulate an actuator node and sensor, possibly on differen
devices on the Desmond network.

* Try entering some text in the **Commandline** sensor.
* Nothing should happen in the **Stdout** actuator.
* Now run `tools/echo.py` in a separate terminal (or in the background).
* Type something else in the **Commandline** sensor.
* Now it should show up at the **Stdout** actuator
