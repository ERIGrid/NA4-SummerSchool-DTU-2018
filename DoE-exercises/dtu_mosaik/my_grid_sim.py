class MyGridSim:
    def __init__(self, V0=230, droop=10):
        self.V0 = V0
        self.droop = droop
        self._curtime = 0
        self.P = {}
        self.calc_val(0)

    def calc_val(self, t):
        assert type(t) is int
        assert t >= self._curtime, "Must step to time of after or at current time: {0}. Was asked to step to {1}".format(t, self._curtime)
        self.Psum = sum(self.P.values())
        self.Pgrid = - self.Psum
        self.V = self.V0 - self.droop * self.Pgrid
