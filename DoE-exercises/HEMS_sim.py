#!/usr/bin/env python
''' Simulation class for the HEMS System

Inputs:
Outputs:
'''

__author__ = "D. Esteban M. Bondy, based on work by Tue V. Jensen"
__copyright__ = "Copyright 2018, DTU"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Esteban Bondy"
__email__ = "bondy@elektro.dtu.dk"
__status__ = "Development"

import mosaik
import mosaik.util
import pandas as pd
import numpy as np
import os
# from dtu_mosaik import *

data_path = 'temp_files/'

def run_simulation(database_name, run_data, verbose=True):
    SIM_CONFIG = {
        'DemandModel': {
            'python': 'dtu_mosaik.mosaik_demand:DemandModel',
        },
        'SimpleGridModel': {
            'python': 'dtu_mosaik.mosaik_grid:SimpleGridModel',
        },
        'CollectorSim': {
            'python': 'dtu_mosaik.collector:Collector',
        },
        'PVModel': {
            'python': 'dtu_mosaik.mosaik_pv:PVModel'
        },
        'BatteryModel': {
            'python': 'dtu_mosaik.mosaik_battery:BatteryModel'
        },
        'Control': {
            'python': 'dtu_mosaik.mosaik_control:Control'
        },
        #'WTModel': {
        #    'python': 'dtu_mosaik.mosaik_wt:WTModel'
        #}
        'NoiseGenerator': {
            'python': 'dtu_mosaik.mosaik_noise:NoiseGenerator'
        }
    }
    run_id = run_data['ID']
    pv1_cap = run_data['pv1_scaling']
    battery_cap = run_data['batt_storage_capacity']
    battery_rate = run_data['batt_charge_capacity']
    change_rate = run_data['controller_change_rate']
    day_type = run_data['climate_conditions']
    random_weather = run_data['random_weather']
    stochastic = run_data['stochastic']
    noise_scale = run_data['noise_scale']
    season = run_data['season']

    seasons = {'summer': 1, 'autumn': 3, 'winter': 5, 'spring': 2}
    demand = seasons[run_data['season']]

    weather_base = {'cloudy': ['/PV715_20180125', '/PV715_20180126', '/PV715_20180127', '/PV715_20180130'],
                    'intermittent': ['/PV715_20180423', '/PV715_20180430', '/PV715_20180820', '/PV715_20180722'],
                    'sunny': ['/PV715_20180730', '/PV715_20180728', '/PV715_20180729', '/PV715_20180721']}
    if random_weather:
        day = weather_base[day_type][np.random.randint(0, 4)]
    else:
        day = weather_base[day_type][0]

    def init_entities(world, pv1_rated_capacity=pv1_cap, batt1_rated_cap=battery_cap,
                      batt1_rate=battery_rate, con_change_rate=change_rate, weather=day, base_demand=demand,
                      noise_scale=noise_scale, filename=data_path+database_name):
        sim_dict = {}
        entity_dict = {}

        # quick check if filepath exists
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        ## Demand
        demand_sim = world.start(
            'DemandModel',
            eid_prefix='demand_',
            step_size=1)
        demand_entity_1 = demand_sim.DemandModel(rated_capacity=base_demand, seriesname='/flexhouse_20180219')
        sim_dict['demand'] = demand_sim
        entity_dict['demand1'] = demand_entity_1

        ## Grid model
        grid_sim = world.start(
            'SimpleGridModel',
            eid_prefix='grid_',
            step_size=1)
        grid_entity_1 = grid_sim.SimpleGridModel(V0=240, droop=0.1)
        sim_dict['grid'] = grid_sim
        entity_dict['grid1'] = grid_entity_1

        ## Collector
        collector_sim = world.start(
            'CollectorSim',
            step_size=60,
            save_h5=True,
            h5_storename='{}_data.h5'.format(filename),
            h5_framename='timeseries/sim_{}'.format(run_id),
            print_results=False)
        collector_entity = collector_sim.Collector()
        sim_dict['collector'] = collector_sim
        entity_dict['collector'] = collector_entity

        ##  PV
        pv_sim = world.start(
            'PVModel',
            eid_prefix='pv_',
            step_size=1)
        sim_dict['pv1'] = pv_sim

        pv_entity_1 = pv_sim.PVModel(
            rated_capacity=pv1_rated_capacity,
            series_name=weather)
        entity_dict['pv1'] = pv_entity_1

        ## WT
        #wt_sim = world.start(
        #    'WTModel',
        #    eid_prefix='wt_',
        #    step_size=1)
        #sim_dict['wt1'] = wt_sim
        #wt_entity_1 = wt_sim.WTModel(
        #    rated_capacity=1,
        #    series_name='/Gaia_20180510')
        #entity_dict['wt1'] = wt_entity_1

        ## Battery
        batt_sim = world.start(
            'BatteryModel',
            eid_prefix='batt_',
            step_size=1)
        batt_entity_1 = batt_sim.BatteryModel(
            rated_capacity=batt1_rated_cap,
            rated_discharge_capacity=batt1_rate,
            rated_charge_capacity=batt1_rate,
            initial_charge_rel=0.5,
            charge_change_rate=0.90,
        )
        sim_dict['batt'] = batt_sim
        entity_dict['batt1'] = batt_entity_1

        ## Controller
        control_sim = world.start(
            'Control',
            eid_prefix='demand_',
            step_size=1)
        control_entity_1 = control_sim.Control(setpoint_change_rate=con_change_rate)

        sim_dict['control'] = control_sim
        entity_dict['control1'] = control_entity_1

        ## "Noisifier"
        noise_injector = world.start(
            'NoiseGenerator',
            eid_prefix='ng_',
            step_size=1)
        noise_entity_1 = noise_injector.NoiseGenerator(scale=noise_scale)

        sim_dict['noise'] = noise_injector
        entity_dict['noise1'] = noise_entity_1

        return sim_dict, entity_dict


    world = mosaik.World(SIM_CONFIG)
    sim_dict, entity_dict = init_entities(world)

    # Connect units to grid busbar
    world.connect(entity_dict['demand1'], entity_dict['grid1'], ('P', 'P'))
    world.connect(entity_dict['pv1'], entity_dict['grid1'], ('P', 'P'))
    world.connect(entity_dict['batt1'], entity_dict['grid1'], ('P', 'P'))

    # Connect controller, note that the grid measurement is passed by a noise injection
    if stochastic:
        world.connect(entity_dict['grid1'], entity_dict['noise1'], ('Pgrid','input'))
        world.connect(entity_dict['noise1'], entity_dict['control1'], ('output', 'Pgrid'))
    else:
        world.connect(entity_dict['grid1'], entity_dict['control1'], ('Pgrid', 'Pgrid'))
    world.connect(entity_dict['control1'], entity_dict['batt1'], ('Pset', 'Pset'), time_shifted=True,
                  initial_data={'Pset': 0.0})
    world.connect(entity_dict['batt1'], entity_dict['control1'], ('relSoC', 'relSoC'))

    # Connect to Collector
    world.connect(entity_dict['batt1'], entity_dict['collector'], ('P', 'BattP'))
    world.connect(entity_dict['batt1'], entity_dict['collector'], ('SoC', 'BattSoC'))
    world.connect(entity_dict['demand1'], entity_dict['collector'], ('P', 'DemP'))
    if stochastic:
        world.connect(entity_dict['noise1'], entity_dict['collector'], ('output', 'GridP'))
    else:
        world.connect(entity_dict['grid1'], entity_dict['collector'], ('Pgrid', 'GridP'))
    world.connect(entity_dict['pv1'], entity_dict['collector'], ('P', 'SolarP'))
    #world.connect(entity_dict['wt1'], entity_dict['collector'], ('P', 'WindP'))

    END = 24*60*60-1 # 24 hours, 1 MosaikTime = 1 second
    world.run(END)
    ## End of simulation

    # # Data processing
    sim_store = pd.HDFStore('temp_files/{}_data.h5'.format(database_name))
    sim_data = sim_store['/timeseries/sim_{}'.format(run_data['ID'])]
    sim_store.close()
    # The measurement at PCC
    # print(sim_data.keys())
    if stochastic:
        grid_balance = sim_data['NoiseGenerator-0.ng__0']
    else:
        grid_balance = sim_data['SimpleGridModel-0.grid__0']
    cost = 0.39  # DKK/kWh
    energy_imported = grid_balance.apply(lambda x: x[x > 0].sum()) / 60
    energy_exported = grid_balance.apply(lambda x: x[x < 0].sum()) / 60
    energy_bill = energy_imported*cost
    maximum_infeed = np.abs(grid_balance).max()
    pv_generated = sim_data['PVModel-0.pv__0']['SolarP'].sum()/60

    self_consumption_index = (pv_generated+energy_exported)/pv_generated

    sim_data = {'ID': [run_id],
                'Energy bill [DKK/kWh]': [energy_bill['GridP']],
                'Max. in-feed [kW]': [maximum_infeed['GridP']],
                'Energy Imported [kWh]': [energy_imported['GridP']],
                'Energy exported [kWh]': [energy_exported['GridP']],
                'Self consumption index': [self_consumption_index['GridP']],
                'pv1_capacity [kW]': [pv1_cap],
                'battery storage capacity [kWh]': [battery_cap],
                'battery charge capacity[kW]': [battery_rate],
                'climate_conditions': [day_type],
                'controller_change_rate': [change_rate],
                'season': [season],
                'File ID/dataframe': ['{}'.format(database_name) + '/' + 'timeseries/sim_{}'.format(run_data['ID'])]}

    run_store = pd.HDFStore('temp_files/runs_summary_{}.h5'.format(database_name))
    run_df = pd.DataFrame(data=sim_data)
    print(run_df)
    run_store['run_{}'.format(run_data['ID'])] = run_df
    run_store.close()
