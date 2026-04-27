
class FloatAccumulator:
    def __init__(self):
        self.value = 0.0
    def __call__(self, increment : int):
        self.value += increment
        return self
    def __str__(self):
        return str(self.value)