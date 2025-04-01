from os import time
from math import inf
from task import MoveToFieldTask, UnsupportedTaskError

class PathfindingLayer:
    GOAL_COMPLETE_EPSILON = 0.01
    TRAJECTORY_SEARCH_INCREMENT = 0.01
    TARGET_ANGLE_COEFF = 0.5
    CLEARANCE_COEFF = 1.2
    SPEED_COEFF = 0.5
    CALCULATE_INTERVAL = 0.25
    TARGET_ANGLE_SMOOTHING_C = 1000
    TARGET_ANGLE_SMOOTHING_K = 1
    CLEARANCE_STEP = 0.05

    def setup(self, setup_info):
        self._obstacles = []
        self._localizer = setup_info.get_localizer()
        self._initial_transform = None

    def is_task_done(self):
        delta = self._get_transform().inv().mul(self._goal)
        return (delta.get_translation().len() < self.GOAL_COMPLETE_EPSILON
            and delta.get_direction().get_angle() < self.GOAL_COMPLETE_EPSILON)

    def update(self, completed):
        now = time()
        if now - self._last_calc_time > self.CALCULATE_INTERVAL:
            self._calculate_path()
            self.lastCalcTime = now
        return iter([HolonomicDriveTask(
            self._current_trajectory.axial,
            -self._current_trajectory.lateral,
            self._current_trajectory.yaw
        )])

    def accept_task(self, task):
        if isinstance(task, MoveToFieldTask):
            self._goal = task.get_goal_transform()
            self.lastCalcTime = -inf
        else:
            raise UnsupportedTaskError(self, task)

    def evaluate_trajectory(self, trajectory):
        target_angle_score = self._evaluate_target_angle(trajectory) * self.TARGET_ANGLE_COEFF
        clearance_score = self._evaluate_clearance(trajectory) * self.CLEARANCE_COEFF
        speed_score = self._evaluate_speed(trajectory) * self.SPEED_COEFF
        return target_angle_score + clearance_score + speed_score

class Trajectory:
    def __init__(self, axial, lateral, yaw):
        self.axial = axial
        self.lateral = lateral
        self.yaw = yaw

class Obstacle:
    def get_distance_to(self, point):
        raise NotImplementedError
