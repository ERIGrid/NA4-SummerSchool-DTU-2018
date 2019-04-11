"""
    A simple data collector that prints all data when the simulator ends.
"""

import collections
import mosaik_api
import pandas as pd

META = {
        'models': {
                'Collector': {
                    'public': True,
                    'any_inputs': True,
                    'params': [],
                    'attrs': [],
                    },
            },
    }

def format_func(x):
    try:
        return '{0:.02f}'.format(x)
    except TypeError:
        return str(x)

class Collector(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid = None
        self.data = collections.defaultdict(
                lambda: collections.defaultdict(list))
        self.time_list=[]

        self.step_size = None

    def init(self, sid, step_size, print_results=True, save_h5=True, h5_storename='collectorstore', h5_framename=None):
        self.step_size = step_size
        self.print_results = print_results
        self.save_h5 = save_h5
        self.h5_storename = h5_storename
        self.h5_framename = h5_framename
        return self.meta

    def create(self, num, model):
        if num>1 or self.eid is not None:
            raise RuntimeError("Can only create one instance of Collector per simulator.")

        self.eid = 'Collector'
        if self.h5_framename is None: self.h5_framename = self.eid
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs):
        data = inputs[self.eid]
        for attr, values in data.items():
            for src, value in values.items():
                self.data[src][attr].append(value)
        self.time_list.append(time)

        return time + self.step_size

    def finalize(self):
        if self.print_results:
            print('Collected data:')
            for sim, sim_data in sorted(self.data.items()):
                print('- {0}'.format(sim))
                for attr, values in sorted(sim_data.items()):
                    print('  - {0}: {1}'.format(attr, list(map(format_func, values))))
        if self.save_h5:
            store = pd.HDFStore(self.h5_storename)
            panel = pd.DataFrame({(unit,attribute): pd.Series(data, index=self.time_list) for unit, datadict in self.data.items() for attribute, data in datadict.items()})
            print(panel)
            print('Saved to store: {0}, dataframe: {1}'.format(self.h5_storename, self.h5_framename))
            store[self.h5_framename] = panel
            store.close()

if __name__ == '__main__':
    mosaik_api.start_simulation(Collector())
