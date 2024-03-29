import random
from mesa import Agent
from enum import Enum

# ---------------------------------------------------------------


class Infra(Agent):
    """
    Base class for all infrastructure components

    Attributes
    __________
    length : float
        the length in meters

    name : string
        the name of the infrastructure

    road name : string
        the road name on which the infrastructure type is located

    vehicle_count : int
        the number of vehicles that are currently in/on (or totally generated/removed by)
        this infrastructure component
    """

    def __init__(self, unique_id, model, length=0,
                 name='Unknown', road_name='Unknown'):
        super().__init__(unique_id, model)
        self.length = length
        self.name = name
        self.road_name = road_name
        self.vehicle_count = 0

    def step(self):
        pass

    def __str__(self):
        return type(self).__name__ + str(self.unique_id)


# ---------------------------------------------------------------
class Bridge(Infra):
    """
    Attributes
    __________
    condition : string
        condition of the bridge

    collapse_chance : float
        the chance that a bridge can collapse, based on the condtion of the bridge

    in_repair : bool
        whether the bridge is in repair
        either True or False

    repair_time : int
        the time it takes to repair a bridge
        is set to 1 day

    delay_time : int
        the delay (in ticks) caused by this bridge
    """

    def __init__(self, unique_id, model, length=0,
                 name='Unknown', road_name='Unknown', condition='Unknown'):
        super().__init__(unique_id, model, length, name, road_name)

        self.condition = condition
        # the collapse chance of a bridge is determined based on the key, value pairs
        # in the dictionary attribute of the model.
        self.collapse_chance = self.model.collapse_dict.get(self.condition)
        self.in_repair = False
        self.repair_time = self.get_repair_time()
        self.delay_time = 0

    def get_delay_time(self):
        """
        Determines the delay time of all bridges with condition X i.e. all bridges that are collapsed,
        depends on the length of the bridge
        """
        if self.condition == "X":
            if self.length > self.model.long_length_threshold:
                self.delay_time = random.triangular(60, 240, 120)
            elif self.length > self.model.medium_length_threshold:
                self.delay_time = random.uniform(45, 90)
            elif self.length > self.model.short_length_threshold:
                self.delay_time = random.uniform(15, 60)
            else:
                self.delay_time = random.uniform(10, 20)
        else:
            pass
        return self.delay_time

    def get_repair_time(self):
        """
        Sets the repair time of a collapsed bridge to 1 day
        """
        self.repair_time = 24*60
        return self.repair_time

    def get_name(self):
        """
        Retrieve bridges name to choose between L/R bridge
        """
        return self.name

    def change_condition(self, new_condition: str):
        """
        Change the condition of a bridge to another condition
        """
        self.condition = new_condition
        return self.condition

    def collapse(self):
        """
        A bridge collapses according to its chance of collapsing.
        A collapsed bridge will get the condition 'X'.
        """
        if self.collapse_chance > random.random():
            self.change_condition("X")
        else:
            pass
        return

    def deteriorate(self):
        """
        A bridge's condition deteriorates
        """

        # you can call this function in the model class,
        # so that for every certain amount of time,bridge conditions deteriorate
        # or for example,if a small storm happens,bridge conditions can deteriorate.
        # please note that deterioration of a bridge is not the same as collapse of a bridge!

        condition_list = ["A", "B", "C", "D", "X"]  # list of all possible bridge conditions
        # if a bridge is already in the worst condition ("X"), it cannot deteriorate any further
        if self.condition == "X":
            pass
        else:
            # for the remaining conditions, deteriorate the bridge by setting the condition to one condition worse
            # get the index in the condition_list of the current bridge condition
            condition_index = condition_list.index(self.condition)
            # increase index by 1 and set that condition to the new current bridge condition
            self.condition = condition_list[condition_index+1]
            return self.condition

    def check_repair(self):
        # if the bridge is not yet in repair, but it is collapsed, set it in repair status
        if not self.in_repair and self.condition == "X":
            self.in_repair = True
            self.delay_time = self.get_delay_time()
        # if bridge is in repair, check if its repair time is already finished
        elif self.in_repair:
            if self.repair_time == 0:
                self.finish_repair()
            else:
                # if the counter is not zero, condition is still collapsed. Counter is decreased with one.
                self.repair_time -= 1
        return

    def finish_repair(self):
        """
        A bridge is repaired
        """

        # repair the bridge by setting the condition to condition A
        # condition before collapse would also be possible. But assumption was made that bridge condition will
        # increase when repairing bridge.
        # if the counter is zero, change the condition
        self.change_condition("A")
        # reset repair time of bridge
        self.repair_time = self.get_repair_time()
        # set in_repair to False
        self.in_repair = False
        # bridge will not be delayed due to repair anymore, so set delay_time back to 0
        self.delay_time = 0
        return

    def step(self):
        # first, the bridge has a chance to collapse. This is done in the collapse function.
        self.collapse()
        # Optional: let the bridge deteriorate
        # self.deteriorate()
        # Next, check if bridge needs repair and if repair is finished.
        self.check_repair()
# ---------------------------------------------------------------


class Link(Infra):
    pass
# ---------------------------------------------------------------


class Sink(Infra):
    """
    Sink removes vehicles

    Attributes
    __________
    vehicle_removed_toggle: bool
        toggles each time when a vehicle is removed
    ...

    """
    vehicle_removed_toggle = False

    def remove(self, vehicle):
        self.model.schedule.remove(vehicle)
        self.vehicle_removed_toggle = not self.vehicle_removed_toggle
        print(str(self) + ' REMOVE ' + str(vehicle))


# ---------------------------------------------------------------
class Source(Infra):
    """
    Source generates vehicles

    Class Attributes:
    -----------------
    truck_counter : int
        the number of trucks generated by ALL sources. Used as Truck ID!

    Attributes
    __________
    generation_frequency: int
        the frequency (the number of ticks) by which a truck is generated

    vehicle_generated_flag: bool
        True when a Truck is generated in this tick; False otherwise
    ...

    """

    truck_counter = 0
    generation_frequency = 5
    vehicle_generated_flag = False

    def step(self):
        if self.model.schedule.steps % self.generation_frequency == 0:
            self.generate_truck()
        else:
            self.vehicle_generated_flag = False

    def generate_truck(self):
        """
        Generates a truck, sets its path, increases the global and local counters
        """
        try:
            agent = Vehicle('Truck' + str(Source.truck_counter), self.model, self)
            if agent:
                self.model.schedule.add(agent)
                agent.set_path()
                Source.truck_counter += 1
                self.vehicle_count += 1
                self.vehicle_generated_flag = True
                print(str(self) + " GENERATE " + str(agent))
        except Exception as e:
            print("Oops!", e.__class__, "occurred.")


# ---------------------------------------------------------------
class SourceSink(Source, Sink):
    """
    Generates and removes trucks
    """
    pass


# ---------------------------------------------------------------
class Vehicle(Agent):
    """

    Attributes
    __________
    speed: float
        speed in meter per minute (m/min)

    step_time: int
        the number of minutes (or seconds) a tick represents
        Used as a base to change unites

    state: Enum (DRIVE | WAIT)
        state of the vehicle

    location: Infra
        reference to the Infra where the vehicle is located

    location_offset: float
        the location offset in meters relative to the starting point of
        the Infra, which has a certain length
        i.e. location_offset < length

    path_ids: Series
        the whole path (origin and destination) where the vehicle shall drive
        It consists the Infras' uniques IDs in a sequential order

    location_index: int
        a pointer to the current Infra in "path_ids" (above)
        i.e. the id of self.location is self.path_ids[self.location_index]

    waiting_time: int
        the time the vehicle needs to wait

    generated_at_step: int
        the timestamp (number of ticks) that the vehicle is generated

    removed_at_step: int
        the timestamp (number of ticks) that the vehicle is removed

    next_infra_name: string
        the name of the next infrastructure object

    driving_time: int
        the driving time on the road for a vehicle
    """

    # 50 km/h translated into meter per min
    speed = 50 * 1000 / 60
    # One tick represents 1 minute
    step_time = 1

    class State(Enum):
        DRIVE = 1
        WAIT = 2

    def __init__(self, unique_id, model, generated_by,
                 location_offset=0, path_ids=None):
        super().__init__(unique_id, model)
        self.generated_by = generated_by
        self.generated_at_step = model.schedule.steps
        self.location = generated_by
        self.location_offset = location_offset
        self.pos = generated_by.pos
        self.path_ids = path_ids
        # default values
        self.state = Vehicle.State.DRIVE
        self.location_index = 0
        self.waiting_time = 0
        self.waited_at = None
        self.removed_at_step = None
        # set an attribute 'next_infra_name' to distinguish the L and R bridge
        self.next_infra_name = None
        self.driving_time = 0

    def __str__(self):
        return "Vehicle" + str(self.unique_id) + \
               " +" + str(self.generated_at_step) + " -" + str(self.removed_at_step) + \
               " " + str(self.state) + '(' + str(self.waiting_time) + ') ' + \
               str(self.location) + '(' + str(self.location.vehicle_count) + ') ' + str(self.location_offset)

    def set_path(self):
        """
        Set the origin destination path of the vehicle
        """
        self.path_ids = self.model.get_random_route(self.generated_by.unique_id)

    def step(self):
        """
        Vehicle waits or drives at each step
        """
        if self.state == Vehicle.State.WAIT:
            self.waiting_time = max(self.waiting_time - 1, 0)
            if self.waiting_time == 0:
                self.waited_at = self.location
                self.state = Vehicle.State.DRIVE

        if self.state == Vehicle.State.DRIVE:
            self.drive()

        """
        To print the vehicle trajectory at each step
        """
        print(self)

    def drive(self):

        # the distance that vehicle drives in a tick
        # speed is global now: can change to instance object when individual speed is needed
        distance = Vehicle.speed * Vehicle.step_time
        distance_rest = self.location_offset + distance - self.location.length

        if distance_rest > 0:
            # go to the next object
            self.drive_to_next(distance_rest)
        else:
            # remain on the same object
            self.location_offset += distance

    def drive_to_next(self, distance):
        """
        vehicle shall move to the next object with the given distance
        """

        self.location_index += 1
        next_id = self.path_ids[self.location_index]
        next_infra = self.model.schedule._agents[next_id]  # Access to protected member _agents

        if isinstance(next_infra, Sink):
            # arrive at the sink
            self.arrive_at_next(next_infra, 0)
            self.removed_at_step = self.model.schedule.steps
            self.driving_time = self.removed_at_step - self.generated_at_step
            self.model.driving_time_of_trucks.append(self.driving_time)
            self.location.remove(self)
            return
        elif isinstance(next_infra, Bridge):
            # check if the next bridge is an L or R bridge
            self.next_infra_name = next_infra.get_name()
            print(str(self.unique_id), 'will go to next bridge:', self.next_infra_name, ', with location ID', next_id)
            if self.next_infra_name[-2:] == '(R':
                self.next_infra_location = next_infra.unique_id
                print(str(self.unique_id), 'now in', str(self.location), 'will skip the "R" bridge in the next step')
                return next_infra

            self.waiting_time = next_infra.get_delay_time()
            if self.waiting_time > 0:
                # arrive at the bridge and wait
                self.arrive_at_next(next_infra, 0)
                self.state = Vehicle.State.WAIT
                return
            # else, continue driving

        if next_infra.length > distance:
            # stay on this object:
            self.arrive_at_next(next_infra, distance)
        else:
            # drive to next object:
            self.drive_to_next(distance - next_infra.length)

    def arrive_at_next(self, next_infra, location_offset):
        """
        Arrive at next_infra with the given location_offset
        """
        self.location.vehicle_count -= 1
        self.location = next_infra
        self.location_offset = location_offset
        self.location.vehicle_count += 1

# EOF -----------------------------------------------------------
