"""
    An entity which simulates grid operation.
"""

import mosaik_api
from itertools import count
from .my_grid_sim import MyGridSim

META = {
    'models': {
        'SimpleGridModel': {
            'public': True,
            'params': [
                'V0', 'droop'],
            'attrs': ['P', 'Pgrid', 'V'],
        },
    },
}


class SimpleGridModel(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=1, eid_prefix="GridE", verbose=False):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        self.verbose = verbose
        return self.meta

    def create(
            self, num, model,
            V0=230, # Volts
            droop=10.0, # 10 volts drop per kW
            ):
        counter = self.eid_counters.setdefault(model, count())
        entities = []


        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = MyGridSim(
                    V0=V0,
                    droop=droop)
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
                if attr == 'P':
                    esim.P = incoming
            esim.calc_val(time)
            if self.verbose:
                print('GRID: Power draw at time {0}: {1}.'.format(time, esim.P))
                print('GRID: Grid stats: Pgrid={0}, Vgrid={1}.'.format(esim.Pgrid, esim.V))

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'P':
                    mydata[attr] = esim.P
                elif attr == 'Pgrid':
                    mydata[attr] = esim.Pgrid
                elif attr == 'V':
                    mydata[attr] = esim.V
                else:
                    raise RuntimeError("GridSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PVSim())

    test = PVSim()
