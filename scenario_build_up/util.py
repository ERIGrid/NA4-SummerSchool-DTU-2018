# from my_batt_sim import MyBattSim

class expando:
    pass

class TSSim:
    def __init__(self, mult, series, Pmax=None, sign=1):
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


