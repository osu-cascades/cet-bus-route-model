class BusHistory:
  def __init__(self, size):
    self.history = []
    self.max_size = size

  def push(self, obs):
    self.history.append(obs)
    if len(self.history) > self.max_size:
      self.history.pop(0)

  def get(self):
    return self.history
