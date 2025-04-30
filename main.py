from flame import Flame, RefineCriteria
import cantera as ct

mech = 'heavy.yaml'
flame1 = Flame(fuel = {'C2H4':1},
    fuel_flow_rate = 88,
    air_flow_rate = 540,
    t_burner = 325,
    t_body = 400,
    pressure = ct.one_atm,
    note = '400 K ethylene')

flame2 = Flame(fuel = {'C2H4':1},
    fuel_flow_rate = 88,
    air_flow_rate = 540,
    t_burner = 325,
    t_body = 500,
    pressure = ct.one_atm,
    note = '500 K ethylene')

flame3 = Flame(fuel = {'C2H4':1},
    fuel_flow_rate = 88,
    air_flow_rate = 540,
    t_burner = 325,
    t_body = 600,
    pressure = ct.one_atm,
    note = '600 K ethylene')

flame4 = Flame(fuel = {'C2H4':1},
    fuel_flow_rate = 88,
    air_flow_rate = 540,
    t_burner = 325,
    t_body = 700,
    pressure = ct.one_atm,
    note = '700 K ethylene')


flames = [flame3, flame4]

for flame in flames:
    flame.solve_mckenna_stabilized(mech, 'results_temperature_11_02_25')