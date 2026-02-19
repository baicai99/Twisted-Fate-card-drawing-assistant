class LegacyPyWinhookBackend:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("legacy backend has been removed; use pynput backend")
