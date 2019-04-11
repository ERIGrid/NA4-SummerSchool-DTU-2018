"""
    An entity which loads a timeseries of relative demand and repeats it when asked
"""

import os
import mosaik_api
import pandas as pd
from numpy import roll
from itertools import count
from .util import TSSim

META = {
    'models': {
        'DemandModel': {
            'public': True,
            'params': ['seriesname', 'rated_capacity'],
            'attrs': ['P'],
        },
    },
}

MY_DIR = os.path.abspath(os.path.dirname(__file__))

class DemandModel(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="DemandE", storefilename=None):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        if storefilename is None:
            # Load default signal store
            self.storefilename = os.path.join(MY_DIR, 'signals.h5')
        else:
            self.storefilename = storefilename
        self.store = pd.HDFStore(self.storefilename)
        self.store.close()
        return self.meta

    def create(self, num, model, seriesname='demand', rated_capacity=10, phase=0):
        counter = self.eid_counters.setdefault(model, count())
        entities = []

        self.store.open()
        series = self.store[seriesname]
        self.store.close()
        if not phase == 0:
            series.values = roll(series.values, phase)

        for _ in range(num):
            eid = '{0}_{1}'.format(self.eid_prefix, next(counter))

            esim = TSSim(rated_capacity, series)
            self.simulators[eid] = esim

            entities.append({'eid': eid, 'type': model})

        return entities

    ###
    #  Functions used online
    ###

    def step(self, time, inputs):
        for eid, esim in self.simulators.items():
            # data = inputs.get(eid, {})
            esim.calc_val(time)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'P':
                    mydata[attr] = -esim.get_val()
                else:
                    raise RuntimeError("DemandSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PPPowerSystem())

    test = DemandSim()
