from ..memory.schemas import SignalEvent


class SignalCollector:
    def collect(self, company):
        raise NotImplementedError


class MockSignalCollector(SignalCollector):
    def __init__(self, events):
        self._events = events

    def collect(self, company):
        return list(self._events)
