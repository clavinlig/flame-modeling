import cantera as ct
import numpy as np
from pathlib import Path
from datetime import datetime

class RefineCriteria:
    def __init__(self, ratio: float = 3.0, slope: float = 0.08, curve: float = 0.3):
        """
        Инициализирует объект с параметрами для уточнения сетки.
        Параметры:
        - ratio: коэффициент соотношения.
        - slope: параметр наклона.
        - curve: параметр кривизны.
        """
        self.ratio = ratio
        self.slope = slope
        self.curve = curve

class Flame:
    def __init__(self, 
                 fuel: dict,
                 fuel_flow_rate: int,
                 air_flow_rate: int,
                 t_burner: int,
                 pressure: int, 
                 note: str,
                 mech : str = 'grimech30.yaml',
                 height: float = 0.023, 
                 d_burner: float = 0.06,
                 t_room: int = 300, 
                 t_body: int = 600, 
                 air: dict = {'O2': 0.21, 'N2': 0.79}):
        
        """
        Инициализирует объект пламени.

        Параметры:
        - fuel: состав топлива (словарь, например, {'CH4': 1.0}).
        - fuel_flow_rate: расход топлива (л/ч).
        - air_flow_rate: расход воздуха (л/ч).
        - t_burner: температура у основания (К).
        - pressure: давление (Па).
        - note: имя/заметка о составе пламени.
        - height: высота пламени (м).
        - t_room: температура окружающей среды (К).
        - t_body: температура тела (К).
        - air: состав воздуха (по умолчанию {'O2': 0.21, 'N2': 0.79}).
        """
        self.fuel = fuel
        self.air = air
        self.fuel_flow_rate = fuel_flow_rate
        self.air_flow_rate = air_flow_rate
        self.t_burner = t_burner
        self.pressure = pressure
        self.t_room = t_room
        self.t_body = t_body
        self.height = height
        self.d_burner = d_burner
        self.note = note
        self.mech = mech
        
    def rate_convert(self, rate: int) -> float:
        """
        Конвертирует расход из л/ч в м³/с.

        Параметры:
        - rate: расход в л/ч.
        Возвращает:
        - Расход в м³/с.
        """
        return rate * 1e-3 / 3600
    
    def mix(self) -> dict:
        """
        Составляет смесь исходя из состава топлива и показателей расходомера.

        Возвращает:
        - Мольный состав (словарь) смеси в эксперименте.
        """

        fuel_flow_rate = self.rate_convert(self.fuel_flow_rate)
        air_flow_rate = self.rate_convert(self.air_flow_rate)

        mixture_composition = {}
        for species, mole_fraction in self.fuel.items():
            mixture_composition[species] = mole_fraction * fuel_flow_rate
        for species, mole_fraction in self.air.items():
            mixture_composition[species] = mole_fraction * air_flow_rate

        total_flow = sum(mixture_composition.values())
        for species in mixture_composition:
            mixture_composition[species] /= total_flow

        return mixture_composition
    
    def calculate_mdot(self) -> float:
        """
        Рассчитывает массовый расход через единицу площади для пламени.

        Параметры:
        - d_burner: диаметр горелки (м).

        Возвращает:
        - mass_flux: массовый расход через единицу площади (кг/(м²·с)).
        """
        fuel_flow_rate = self.rate_convert(self.fuel_flow_rate)
        air_flow_rate = self.rate_convert(self.air_flow_rate)
        
        burner_area = np.pi * self.d_burner ** 2 / 4  # (m^2)
        gas = ct.Solution(self.mech)
    
        mix_comp = self.mix()
    
        gas.TPX = self.t_room, self.pressure, mix_comp
        total_flow = fuel_flow_rate + air_flow_rate 
        mass_flux = total_flow * gas.density / burner_area
        return mass_flux

    def solve_mckenna_stabilized(self,
                                mech: str,
                                output_dir: str,
                                refine_criteria: RefineCriteria = RefineCriteria(),
                                loglevel: int = 1):
        """
        Решает задачу стабилизированного пламени с использованием Cantera.

        Параметры:
        - mech: путь к механизму реакции (файл YAML).
        - refine_criteria: словарь с параметрами для уточнения сетки.
        - loglevel: уровень логирования (по умолчанию 1).
        """
        mixture = self.mix() 
        gas = ct.Solution(mech)
        gas.TPX = self.t_room, self.pressure, mixture

        mdot = self.calculate_mdot()
        gas.TP = self.t_burner, self.pressure

        # Create the stagnation flow object with a non-reactive surface
        
        sim = ct.ImpingingJet(gas=gas, width=self.height)
        sim.inlet.mdot = mdot
        sim.surface.T = self.t_body 
        sim.set_grid_min(2e-5) 
        sim.set_refine_criteria(
            ratio=refine_criteria.ratio,
            slope=refine_criteria.slope,
            curve=refine_criteria.curve
            # prune=grid_refine_criteria.prune #убир узел при дост гладкости
        )
        sim.set_initial_guess(products='equil')  # assume adiabatic equilibrium products
        sim.radiation_enabled = True #учит. изл.
        sim.solve(loglevel, auto=True)

        output_dir = Path(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # write the velocity, temperature, and mole fractions to a CSV file
        sim.save(output_dir / f"{self.note.replace(' ', '_')}_X.csv", basis="mole", overwrite=True)
        sim.save(output_dir / f"{self.note.replace(' ', '_')}_Y.csv", basis="mass", overwrite=True)
        if loglevel > 0: 
            sim.show_stats()

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # log
        log_entry = (
            f"Date and time: {current_time}\n"
            f"Flame Data: {self.__dict__}\n"
            f"File with results: {self.note}.yaml, "
            f"{self.note}_state, "
            f"{self.note}_X.csv, "
            f"{self.note}_Y.csv\n"
            "----------------------------------------\n"
        )
        with open(output_dir / 'calculations_log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)