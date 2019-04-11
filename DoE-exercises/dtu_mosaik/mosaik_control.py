"""
    An entity which loads a timeseries of relative PV production and outputs it when asked
"""

import mosaik_api
from itertools import count
from statistics import mean

META = {
    'models': {
        'Control': {
            'public': True,
            'params': [
                'setpoint_change_rate'],
            'attrs': ['Pgrid', 'Pset', 'relSoC'],
        },
    },
}


class Control(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="ControlE", verbose=False):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        self.verbose = verbose
        return self.meta

    def create(
            self, num, model,
            setpoint_change_rate=0.50):
        counter = self.eid_counters.setdefault(model, count())
        entities = []


        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = {'Pset': 0, 'Pgrid': 0, 'relSoC': 10, 'rate': setpoint_change_rate}
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
                if self.verbose: print("Incoming data:{0}".format(incoming))
                if attr == 'Pgrid':
                    Pgrid, Pset, r = esim['Pgrid'], esim['Pset'], esim['rate']
                    # If multiple units provide us with a measurement,
                    # take the mean.
                    Pgrid = mean(incoming.values())
                    newPset = r * Pgrid + Pset
                    if esim['relSoC'] < 0.01 and newPset > 0:
                        newPset = 0.0
                    elif esim['relSoC'] > 0.99 and newPset < 0:
                        newPset = 0.0
                    esim['Pset'] = newPset
                    esim['Pgrid'] = Pgrid
                    if self.verbose: print("Found grid consumption {0}, setting set point {1} (delta={2}).".format(Pgrid, newPset, newPset - Pset))
                if attr == 'relSoC':
                    esim['relSoC'] = sum(incoming.values())
            # esim.calc_val(time)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'Pgrid':
                    mydata[attr] = esim['Pgrid']
                elif attr == 'Pset':
                    mydata[attr] = esim['Pset']
                elif attr == 'relSoC':
                    mydata[attr] = esim['relSoC']
                else:
                    raise RuntimeError("Control {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(ControlSim())

    test = Control()
