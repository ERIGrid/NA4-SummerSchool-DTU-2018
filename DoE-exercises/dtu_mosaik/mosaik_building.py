"""
    An entity which mimics a building with an internal temperature and constant proportional heat loss.
    Note that parameters which couple to the temperature (proportional to x, zs) are expressed in degrees celcius per hour.
    That is, they state how much a value of, e.g. x=1.0 will cause the temperature to change over the course of 1 hour.

    @inputs & outputs:
        x: Current heater setting (in [0,1])
        T_amb: Ambient temperature [degC]
        zs: Solar irradiation (in [0,1], 1 => full sun)
    @outputs:
        P: Current power draw from electric heater
        T_int: Current internal temperature
"""

import mosaik_api
import os
import pandas as pd
from numpy import roll
from itertools import count
from util import MyBuildingSim

META = {
    'models': {
        'BuildingModel': {
            'public': True,
            'params': [
                'heat_coeff', 'solar_heat_coeff', 'insulation_coeff',
                'init_T_int', 'init_T_amb', 'heater_power'],
            'attrs': ['P', 'x', 'T_int', 'zs', 'T_amb'],
        },
    },
}

MY_DIR = os.path.abspath(os.path.dirname(__file__))

class BuildingSim(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="PVe", storefilename=None):
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

    def create(
            self, num, model,
            heat_coeff=9.0, solar_heat_coeff=6.0,
            insulation_coeff=0.2, init_T_int=12.0,
            init_T_amb=12.0, heater_power=5.0):
        counter = self.eid_counters.setdefault(model, count())
        entities = []

        for _ in range(num):
            eid = '%s_%s' % (self.eid_prefix, next(counter))

            esim = HouseSim(
                    heat_coeff=heat_coeff,
                    solar_heat_coeff=solar_heat_coeff,
                    insulation_coeff=insulation_coeff,
                    init_T_int=init_T_int,
                    init_T_amb=init_T_amb,
                    heater_power=heater_power)
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
                if attr == 'x':
                    newX = min(val for val in incoming.values())
                    esim.x = newX
                elif attr == 'T_amb':
                    newT_amb = min(val for val in incoming.values())
                    esim.T_amb = newT_amb
                elif attr == 'zs':
                    newzs = min(val for val in incoming.values())
                    esim.zs = newzs
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
                elif attr == 'x':
                    mydata[attr] = esim.x
                elif attr == 'T_int':
                    mydata[attr] = esim.T_int
                elif attr == 'zs':
                    mydata[attr] = esim.zs
                elif attr == 'T_amb':
                    mydata[attr] = esim.T_amb
                else:
                    raise RuntimeError("PVSim {0} has no attribute {1}.".format(eid, attr))
            data[eid] = mydata
        return data

if __name__ == '__main__':
    # mosaik_api.start_simulation(PVSim())

    test = BuildingSim()
