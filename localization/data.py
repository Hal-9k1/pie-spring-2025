from localization import LocalizationData


class AbstractFinDiffLocalizationData(LocalizationData):
    def __init__(self, epsilon):
        self._epsilon = epsilon

    def get_position_probability_dx(self, pos):
        return ((self.get_position_probability(pos.add(Vec2(self._epsilon, 0)))
            - self.get_position_probability(pos))
            / self._epsilon)

    def get_position_probability_dy(self, pos):
        return ((self.get_position_probability(pos.add(Vec2(0, self._epsilon)))
            - self.get_position_probability(pos))
            / self._epsilon)

    def get_position_probability_dx_gradient(self, pos):
        z = self.get_position_probability_dx(pos)
        wrtX = (self.get_position_probability_dx(pos.add(Vec2(self._epsilon, 0))) - z) / self._epsilon
        wrtY = (self.get_position_probability_dx(pos.add(Vec2(0, self._epsilon))) - z) / self._epsilon
        return Vec2(wrtX, wrtY)

    def get_position_probability_dy_gradient(self, pos):
        z = self.get_position_probability_dy(pos)
        wrtX = (self.get_position_probability_dy(pos.add(Vec2(self._epsilon, 0))) - z) / self._epsilon
        wrtY = (self.get_position_probability_dy(pos.add(Vec2(0, self._epsilon))) - z) / self._epsilon
        return Vec2(wrtX, wrtY)

    def get_rotation_probability_dx(self, rot):
        return ((self.get_rotation_probability(rot + self._epsilon)
            - self.get_rotation_probability(rot))
            / self._epsilon)

    def get_rotation_probability_dx2(self, rot):
        return (self.get_rotation_probability_dx(rot + self._epsilon)
            - self.get_rotation_probability_dx(rot)) / self._epsilon


class SqFalloffLocalizationData(AbstractFinDiffLocalizationData):
    def __init__(self, epsilon, transform, accuracy, position_precision, rotation_precision):
        super().__init__(epsilon)
        self._transform = transform
        self._accuracy = accuracy
        self._position_precision = position_precision
        self._rotation_precision = rotation_precision

    def get_position_probability(self, pos):
        diff = self._transform.get_translation().mul(-1).add(pos)
        return self._accuracy / ((diff.dot(diff) * self._position_precision) + 1)

    def get_rotation_probability(self, rot):
        diff = rot - self._transform.get_direction().get_angle()
        return self._accuracy / (diff * diff * self._rotation_precision + 1)
