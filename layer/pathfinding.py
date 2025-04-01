from os import time
from math import inf
from math import sin
from math import cos
from math import sqrt
from math import copysign
from task import MoveToFieldTask, UnsupportedTaskError
from matrix import Mat3

def _signum(num):
    return copysign(1, num)

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

    def _evaluate_trajectory(self, trajectory):
        target_angle_score = self._evaluate_target_angle(trajectory) * self.TARGET_ANGLE_COEFF
        clearance_score = self._evaluate_clearance(trajectory) * self.CLEARANCE_COEFF
        speed_score = self._evaluate_speed(trajectory) * self.SPEED_COEFF
        return target_angle_score + clearance_score + speed_score

    def evaluate_target_angle(self, t):
        final_transform = self._get_trajectory_transform(t, 1)
        final_direction = final_transform.get_direction()
        final_delta = final_transform.get_translation().mul(-1).add(goal.get_translation())
        angle = final_direction.angle_with(final_delta)
        return self.TARGET_ANGLE_SMOOTHING_C / (angle + self.TARGET_ANGLE_SMOOTHING_K)

    def _evaluate_clearence(self, t):
        min_clearence = inf
        for frac in range(0, 1, self.CLEARENCE_STEP):
            translation = self._get_trajectory_transform(t, frac).get_translation()
            for obstacle in self._obstacles:
                clearance_to_obstacle = obstacle.get_distance_to(translation)
                if min_clearence > clearance_to_obstacle:
                    min_clearence = clearance_to_obstacle
        return min_clearence

    def _evaluate_speed(self, t):
        return self._get_trajectory_velocity(t, 1).get_translation().len()

    def _calculate_path(self):
        if self._initial_transform == None:
            self._initial_velocity = Mat3.identity()
            self._initial_transform = self._get_transform()
        else:
            new_transform = self._get_transform()
            delta = self._initial_transform.inv().mul(new_transform)
            self._initial_velocity = Mat3.from_transform(
                Mat2.from_angle(delta.get_direction().get_angle() / self._CALCULATE_INTERVAL),
                delta.get_translation().mul(1 / self._CALCULATE_INTERVAL)
            )
            self._initial_transform = new_transform

        # Keeps track of the best-scored trajectory and the score it had.
        best_trajectory = None
        best_score = -inf

        # Represents bounds of the search space.
        max_bounds = Trajectory(1, 1, 1)
        min_bounds = Trajectory(-1, -1, -1)

        inc = self._TRAJECTORY_SEARCH_INCREMENT

        # Veeeeeeery slow search loop.
        for a in range(min_bounds.get_axial(), max_bounds.get_axial(), inc):
            for l in range(min_bounds.get_lateral(), max_bounds.get_lateral(), inc):
                for y in range(min_bounds.get_yaw(), max_bounds.get_yaw(), inc):
                    t = Trajectory(a, l, y)
                    if not self._check_dynamic_window(t):
                        continue
                    score = self._evaluate_trajectory(t)
                    if score > best_score:
                        best_score = score
                        best_trajectory = t
        if best_score == -inf:
            # Dynamic window was empty of trajectories (all valid ones interesct obstacles)
            # Spin until the dynamic window isn't empty
            best_trajectory = new Trajectory(0, 0, 1)
        self._current_trajectory = best_trajectory

    def _check_dynamic_window(self, t) {
        for frac in range(0, 1, self._CLEARENCE_STEP):
            translation = self._get_trajectory_transform(t, frac).get_translation()
            for obstacle in self._obstacles:
                clearance_to_obstacle = obstacle.get_distance_to(translation)
                if clearance_to_obstacle < 0:
                    return False
        return abs(t.get_axial()) + abs(t.get_lateral()) + abs(t.get_yaw()) < 1

    def add_obstacle(self, obstacle):
        self._obstacles.add(obstacle)

    def _get_trajectory_transform(self, t, frac):
        za = t.get_axial()
        zl = t.get_lateral()
        zth = t.get_yaw()
        tf = frac * CALCULATE_INTERVAL
        x0 = self._initial_transform.get_translation().get_x()
        vx0 = self._initial_velocity.get_translation().get_x()
        y0 = self._initial_transform.get_translation().get_y()
        vy0 = self._initial_velocity.get_translation().get_y()
        vth0 = self._initial_velocity.get_direction().get_angle()
        th0 = self._initial_transform.get_direction().get_angle()

        x = (x0 + vx0 * tf
            + tf * (
                za * (sin(th0 + vth0 * tf + zth * tf * tf / 2) - sin(th0))
                + zl * (cos(th0 + vth0 * tf + zth * tf * tf / 2) - cos(th0)))
            / sqrt(vth0 * vth0 - 2 * zth * th0))
        y = (y0 + vy0 * tf
            + tf * (
                -za * (cos(th0 + vth0 * tf + zth * tf * tf / 2) - cos(th0))
                + zl * (sin(th0 + vth0 * tf + zth * tf * tf / 2) - sin(th0)))
            / sqrt(vth0 * vth0 - 2 * zth * th0))
        th = th0 + vth0 * tf + zth * tf * tf / 2

        return Mat3.from_transform(Mat2.from_angle(th), Vec2(x, y))

    def _get_trajectory_velocity(self, t, frac):
        tf = frac * self._CALCULATE_INTERVAL
        return Mat3.from_transform(
            Mat2.from_angle(t.get_yaw() * tf + self._initial_velocity.get_direction().get_angle()),
            Vec2(t.get_axial(), t.get_lateral()).mul(tf).add(self._initial_velocity.get_translation())
        )

    def _get_transform():
        return self._localizer.resolve_transform()


class Trajectory:
    def __init__(self, axial, lateral, yaw):
        self._axial = axial
        self._lateral = lateral
        self._yaw = yaw

    def get_axial(self):
        return self._axial

    def get_lateral(self):
        return self._lateral

    def get_yaw(self):
        return self._yaw


class Obstacle(ABC):
    def get_distance_to(self, point):
        raise NotImplementedError


class DynamicObstacle(Obstacle):
    def __init__(self, transform, size):
        self._transform = transform
        self._size = size

    def get_distance_to(self, point):
        delta = self._transform.get_translation().add(point.mul(-1))
        axial_proj = self._transform.get_direction().proj(delta).len()
        lateral_proj = self._transform.get_direction().get_perpendicular().proj(delta).len()
        if lateral_proj < self._size / 2:
            return axial_proj
        ep1 = self._transform.mul(new Vec2(0, size / 2))
        ep2 = self._transform.mul(new Vec2(0, -size / 2))
        return min(ep1.add(point.mul(-1)).len(), ep2.add(point.mul(-1)).len())

class StaticObstacle(Obstacle):
    def __init__(self, transform, size):
        self._transform = transform
        self._size = size

    def get_distance_to(self, point):
        p = self._transform.inv().mul(point)
        m1 = self._size.get_y() / self._size.get_x()
        m2 = -m1
        use_height = _signum(p.get_y() - m1) == _signum(p.get_y() - m2)
        dim = self._size.get_y() if use_height else self._size.get_x()
        return p.len() - dim / (2 * cos(p.get_angle()))
