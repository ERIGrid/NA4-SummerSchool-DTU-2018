"""
    An entity which loads a timeseries of relative PV production and outputs it when asked
"""

import mosaik_api
from itertools import count
from .util import MyBattSim

META = {
    'models': {
        'BatteryModel': {
            'public': True,
            'params': [
                'rated_capacity', 'rated_charge_capacity', 'rated_discharge_capacity',
                'roundtrip_efficiency', 'initial_charge_rel', 'charge_change_rate'],
            'attrs': ['P', 'Pset', 'SoC', 'relSoC'],
        },
    },
}


class BatteryModel(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="BattE"):
        self.step_size = step_size
        self.eid_prefix = eid_prefix
        return self.meta

    def create(
            self, num, model,
            rated_capacity=10,
            rated_discharge_capacity=20,
            rated_charge_capacity=20,
            roundtrip_efficiency=0.96,
            initial_charge_rel=0.50,
            charge_change_rate=0.90,
            dt=1.0/(60 * 60)):
        counter = self.eid_counters.setdefault(model, count())
        entities = []


        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = MyBattSim(
                rated_capacity=rated_capacity,
                rated_discharge_capacity=rated_discharge_capacity,
                rated_charge_capacity=rated_charge_capacity,
                roundtrip_efficiency=roundtrip_efficiency,
                initial_charge_rel=initial_charge_rel,
                charge_change_rate=charge_change_rate,
                dt=dt
                )
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
                if attr == 'Pset':
                    newPset = min(val for val in incoming.values())
                    esim.Pset = newPset
            esim.calc_val(time)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}
            for attr in requests:
                if attr == 'P':
                    mydata[attr] = esim.P
                elif attr == 'Pset':
                    mydata[attr] = esim.Pset
                elif attr == 'SoC':
                    mydata[attr] = esim.SoC
                elif attr == 'relSoC':
                    mydata[attr] = esim.relSoC
                else:
                    raise RuntimeError("BattSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PVSim())

    test = PVSim()
