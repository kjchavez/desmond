from desmond import thought

class Sensor(thought.DesmondNode):
    """ A Sensor is DesmondNode with no inputs. It only produces data. """
    def __init__(self, name, OutputType, transport="tcp"):
        super(Sensor, self).__init__(name, [], OutputType, transport=transport)
