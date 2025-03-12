
class Vec3:
    def __init__(self, x, y, z):
        self._vec = [x, y, z]

    def get_x(self):    
        return self._vec[0]
    
    def get_y(self):
        return self._vec[1]
    
    def get_z(self):
        return self._vec[2]
    
    def dot(self, other):
        return self._vec[0] * other.get_x() + self._vec[1] * other.get_y() + self._vec[2] * other.get_z()
    
    def get(self, index):
        if index < 0 or index > 2:
            raise ValueError(f"Bad index {index}")
        return self._vec[index]