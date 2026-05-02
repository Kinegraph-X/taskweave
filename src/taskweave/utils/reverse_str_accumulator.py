
class ReverseStrAccumulator:
    def __init__(self, value = ""):
        self.value = value
    def __call__(self, prefix : str):
        self.value = f"{prefix}{self.value}"
        return self
    def __str__(self):
        return self.value