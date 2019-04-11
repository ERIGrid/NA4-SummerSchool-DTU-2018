"""
    An entity which loads a timeseries of relative PV production and outputs it when asked
"""

import mosaik_api
import pandas as pd
from itertools import count
from util import TSSim

META = {
    'models': {
        'PVModel': {
            'public': True,
            'params': ['series_name', 'rated_capacity'],
            'attrs': ['P', 'Pav', 'Pmax'],
        },
    },
}


class PVModel(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="PVe", storefilename='signals.h5'):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        self.storefilename = storefilename
        self.store = pd.HDFStore(storefilename)
        self.store.close()
        return self.meta

    def create(self, num, model, series_name='pv', rated_capacity=10):
        counter = self.eid_counters.setdefault(model, count())
        entities = []

        self.store.open()
        series = self.store[series_name]
        self.store.close()

        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = TSSim(rated_capacity, series)
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
                if attr == 'Pmax':
                    newPmax = min(val for val in incoming.values())
                    self.entityparams[eid]
            esim.calc_val(time)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'P':
                    mydata[attr] = esim.get_val()
                elif attr == 'Pmax':
                    mydata[attr] = esim.get_Pmax()
                elif attr == 'Pav':
                    mydata[attr] = esim.get_val_nomax()
                elif attr == 'Prated':
                    mydata[attr] = esim.get_mult()
                else:
                    raise RuntimeError("PVSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PVSim())

    test = PVSim()
