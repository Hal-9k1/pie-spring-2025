import numpy as np

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

    def __init__(self):
        self.goal = np.eye(3)
        self.obstacles = []
        self.currentTrajectory = None
        self.lastCalcTime = 0
        self.initialTransform = np.eye(3)
        self.initialVelocity = np.eye(3)
        self.localizer = None

    def setup(self, setup_info):
        self.localizer = setup_info.get('localizer')

    def is_task_done(self):
        delta = np.linalg.inv(self.get_transform()) @ self.goal
        translation_len = np.linalg.norm(delta[:2, 2])
        direction_angle = np.arctan2(delta[1, 0], delta[0, 0])
        return translation_len < self.GOAL_COMPLETE_EPSILON and abs(direction_angle) < self.GOAL_COMPLETE_EPSILON

    def update(self, completed):
        now = self.current_time()
        if now - self.lastCalcTime > self.CALCULATE_INTERVAL:
            self.calculate_path()
            self.lastCalcTime = now
        return [(self.currentTrajectory.axial, -self.currentTrajectory.lateral, self.currentTrajectory.yaw)]

    def accept_task(self, task):
        if isinstance(task, dict) and task.get('type') == 'MoveToFieldTask':
            self.goal = task.get('goal_transform')
            self.lastCalcTime = self.current_time() - self.CALCULATE_INTERVAL

    def evaluate_trajectory(self, trajectory):
        target_angle_score = self.evaluate_target_angle(trajectory) * self.TARGET_ANGLE_COEFF
        clearance_score = self.evaluate_clearance(trajectory) * self.CLEARANCE_COEFF
        speed_score = self.evaluate_speed(trajectory) * self.SPEED_COEFF
        return target_angle_score + clearance_score + speed_score

    def current_time(self):
        import time
        return time.time()

class Trajectory:
    def __init__(self, axial, lateral, yaw):
        self.axial = axial
        self.lateral = lateral
        self.yaw = yaw

class Obstacle:
    def get_distance_to(self, point):
        raise NotImplementedError
