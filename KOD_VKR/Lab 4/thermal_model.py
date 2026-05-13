"""
Python model 'thermal_model.py'
Translated using PySD
"""

from pathlib import Path

from pysd.py_backend.statefuls import Integ
from pysd import Component

__pysd_version__ = "3.14.3"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 500,
    "time_step": lambda: 1,
    "saveper": lambda: 1,
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(name="FINAL TIME", comp_type="Constant", comp_subtype="Normal")
def final_time():
    return __data["time"].final_time()


@component.add(name="INITIAL TIME", comp_type="Constant", comp_subtype="Normal")
def initial_time():
    return __data["time"].initial_time()


@component.add(name="TIME STEP", comp_type="Constant", comp_subtype="Normal")
def time_step():
    return __data["time"].time_step()


@component.add(name="SAVEPER", comp_type="Constant", comp_subtype="Normal")
def saveper():
    return __data["time"].saveper()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="Room Temperature",
    units="Degree C",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_room_temperature": 1},
    other_deps={
        "_integ_room_temperature": {
            "initial": {"initial_temperature": 1},
            "step": {
                "heat_gain_from_people": 1,
                "heat_loss": 1,
                "air_heat_capacity": 1,
            },
        }
    },
)
def room_temperature():
    return _integ_room_temperature()


_integ_room_temperature = Integ(
    lambda: (heat_gain_from_people() - heat_loss()) / air_heat_capacity(),
    lambda: initial_temperature(),
    "_integ_room_temperature",
)


@component.add(
    name="Heat Gain from People",
    units="Watt",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"people_count": 1, "heat_per_person": 1},
)
def heat_gain_from_people():
    return people_count() * heat_per_person()


@component.add(
    name="Heat Loss",
    units="Watt",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "room_temperature": 1,
        "outside_temperature": 1,
        "insulation_factor": 1,
    },
)
def heat_loss():
    return (room_temperature() - outside_temperature()) * insulation_factor()


@component.add(
    name="people_count", units="person", comp_type="Constant", comp_subtype="Normal"
)
def people_count():
    return 0


@component.add(
    name="Heat per Person",
    units="Watt/person",
    comp_type="Constant",
    comp_subtype="Normal",
)
def heat_per_person():
    """
    теплоотдача человека, норма 100
    """
    return 80


@component.add(
    name="Air Heat Capacity",
    units="Joule/Degree C",
    comp_type="Constant",
    comp_subtype="Normal",
)
def air_heat_capacity():
    """
    чем меньше это число, тем меньше энергии нужно, чтобы поднять температуру на 1 градус
    """
    return 50000


@component.add(
    name="Outside Temperature",
    units="Degree C",
    comp_type="Constant",
    comp_subtype="Normal",
)
def outside_temperature():
    """
    уличная температура
    """
    return 20


@component.add(
    name="Insulation Factor",
    units="Watt/Degree C",
    comp_type="Constant",
    comp_subtype="Normal",
)
def insulation_factor():
    """
    скорость остывания помещения, норма 15-20
    """
    return 20


@component.add(
    name="Initial Temperature",
    units="Degree C",
    comp_type="Constant",
    comp_subtype="Normal",
)
def initial_temperature():
    return 22


@component.add(
    name="AC_POWER", units="Watt", comp_type="Constant", comp_subtype="Normal"
)
def ac_power():
    """
    мощность кондиционера (0 - выключен, 500 - включен)
    """
    return 0
