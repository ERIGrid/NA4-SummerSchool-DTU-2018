import mosaik_api
import os
from numpy.random import triangular
from itertools import count
from .util import NoiseDistorter
from statistics import mean

META = {
    'models': {
        'NoiseGenerator': {
            'public': True,
            'params': ['distribution','scale'],
            'attrs': ['input','output'],
        },
    },
}

MY_DIR = os.path.abspath(os.path.dirname(__file__))


class NoiseGenerator(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="noise"):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model, distribution=triangular, scale=0):
        counter = self.eid_counters.setdefault(model, count())
        entities = []

        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = NoiseDistorter(distribution=distribution, scale=scale)
            self.simulators[eid] = esim

            entities.append({'eid': eid, 'type': model})

        return entities

    ###
    #  Functions used online
    ###

    def step(self, time, inputs):
        for eid, esim in self.simulators.items():
            data = inputs.get(eid, {})
            for attr, incoming in data.items():
                if attr == 'input':
                    signals = incoming.values()
                    signal = mean(signals)
                    esim.distort(signal)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'output':
                    mydata[attr] = esim.get_val()
                elif attr == 'input':
                    mydata[attr] = esim.get_input()
                else:
                    raise RuntimeError("NoiseGenerator {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PVSim())

    test = NoiseGenerator()