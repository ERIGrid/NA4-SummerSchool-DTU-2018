class expando:
    pass

class TSSim:
    def __init__(self, mult, series, Pmax=None, sign=1, phase=0):
        self.mult = mult
        self.series = series
        self.sign = sign
        if Pmax == None:
            self.Pmax = 1e100
        self.calc_val(0)

    def calc_val(self, t):
        self.cur_t = t
        self.val_nomax = self.sign * self.mult * self.series[t]
        self.val = max(min(self.val_nomax, self.Pmax), -self.Pmax)

    def get_val(self):
        return self.val

    def get_val_nomax(self):
        return self.val_nomax

    def get_Pmax(self):
        return self.Pmax

    def get_Prated(self):
        return self.mult

class NoiseDistorter:
    from numpy.random import triangular

    def __init__(self, distribution=triangular, lower=-1.0, mid=0, upper=0.7, scale=0):
        self.distribution = distribution
        self.lower = lower*scale
        self.mid = mid*scale
        self.upper = upper*scale

        self.output = 0
        self.x = 0

    def distort(self, new_x):
        self.output = float(new_x) + self.distribution(self.lower, self.mid, self.upper)
        self.x = new_x

    def get_val(self):
        return self.output

    def get_input(self):
        return self.x


class MyBuildingSim:
    def __init__(self,
            heat_coeff=12.0, solar_heat_coeff=6.0,
            insulation_coeff=0.2, init_T_int=22.0,
            init_T_amb=12.0, heater_power=5.0, dt=1.0/3600):

        # Parrameters
        self.heat_coeff = heat_coeff
        self.solar_heat_coeff = solar_heat_coeff
        self.insulation_coeff = insulation_coeff
        self.init_T_int = init_T_int
        self.init_T_amb = init_T_amb
        self.heater_power = heater_power
        self.dt = dt # 1 MosaikTime = 1s
        self.curtime=0

        # Variables
        self.T_int = init_T_int
        self.T_amb = init_T_amb
        self.zs = 0
        self._x = 0
        self._P = 0

    def calc_val(self, t):
        assert type(t) is int
        assert t >= self.curtime, "Must step to time of after or at current time: {0}. Was asked to step to {1}".format(t, self.curtime)
        for _ in range(t - self.curtime):
            self._do_state_update()
        self.curtime = t

    def _do_state_update(self):
        self.T_int =  self.T_int + self.dt*(
                self.insulation_coeff * (self.T_amb - self.T_int) \
                + self.solar_heat_coeff * self.zs\
                + self.heat_coeff * self._x)

    @property
    def P(self):
        return self._P

    @P.setter
    def P(self, newP):
        self._P = newP
        self._x = newP / self.heater_power

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, newx):
        self._x = newx
        self.P = self.heater_power * newx

class MyBattSim:
    def __init__(
            self,
            rated_capacity=10,
            rated_discharge_capacity=20,
            rated_charge_capacity=20,
            roundtrip_efficiency=0.96,
            initial_charge_rel=0.50,
            charge_change_rate=0.90,
            dt=1.0/(60*60)):
        """
            Battery simulator.
            Time is assumed to proceed in integer steps.
            @input:
                rated_capacity: Max volume of charge [kWh]
                rated_discharge_capacity: Max output power [kW]
                rated_charge_capacity: Max input power [kW]
                roundtrip_efficiency: Total roundtrip efficiency [0.0-1.0]
                initial_charge_rel: Charge at time 0 relative to max [0.0 - 1.0]
                charge_change_rate: Rate at which charge follows setpoint,
                    1.0= instant following. [0.0 - 1.0]
                dt: number of hours per time step [h] (default: 1 sec per time step)
        """
        self.rated_capacity = rated_capacity
        self.rated_discharge_capacity = rated_discharge_capacity
        self.rated_charge_capacity = rated_charge_capacity
        self.eta = roundtrip_efficiency
        self.alpha = charge_change_rate

        # Internal variables
        self.curtime = 0 # Time is assumed to step in integer steps
        self.dt = dt
        self._P = 0
        self._Pset = 0
        self._charge = initial_charge_rel * rated_capacity

        # Externally visible variables
        self.Pext = 0
        self.Psetext = 0
        self.SoC = self._charge
        self.relSoC = self._charge / self.rated_capacity

    def calc_val(self, t):
        """
        """
        assert type(t) is int
        assert t >= self.curtime, "Must step to time of after or at current time: {0}. Was asked to step to {1}".format(t, self.curtime)
        self._ext_to_int() # Translate external state to internal state
        for _ in range(t - self.curtime):
            self._do_state_update()
        self._int_to_ext() # Translate internal state to external state
        self.curtime = t

    def _do_state_update(self):
        # Current power will slowly rise towards setpoint
        P = self.alpha * self._Pset + (1 - self.alpha) * self._P
        self._P = self._limit_P(P)
        self._update_charge()


    def _limit_P(self, P):
        # Limit according to bounds
        P = min(max(P, -self.rated_discharge_capacity), self.rated_charge_capacity)
        # Limit to available charge, roundtrip eff. is applied to output
        P = min(
                max(P, -self._charge * self.eta / self.dt), # Cannot discharge more than we have
                (self.rated_capacity - self._charge)/ self.dt) # Cannot overfill
        return P

    def _update_charge(self):
        C = self._charge + self._P / (self.eta if self._P>0 else 1) * self.dt
        self._charge = min(
                max(C, 0),
                self.rated_capacity)

    def _ext_to_int(self):
        self._Pset = - self.Psetext

    def _int_to_ext(self):
        self.Pext = - self._P
        self.SoC = self._charge
        self.relSoC = self._charge / self.rated_capacity

    # Getter/setters for external users
    @property
    def P(self):
        return self.Pext

    @property
    def Pset(self):
        return self.Psetext

    @Pset.setter
    def Pset(self, newPset):
        self.Psetext = min(self.rated_discharge_capacity,
                max(newPset, -self.rated_charge_capacity))
