
class StrAccumulator:
    def __init__(self):
        self.value = ""
    def __call__(self, increment : str):
        self.value += increment
        return self
    def __str__(self):
        return self.value