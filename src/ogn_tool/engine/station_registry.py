class StationRegistry:
    """
    Minimal station registry placeholder.

    This class keeps track of known stations during RF analysis.
    It can later be extended with real metadata, caching and network topology.
    """

    def __init__(self):
        self._stations = {}

    def register(self, station_id, metadata=None):
        self._stations[station_id] = metadata or {}

    def get(self, station_id):
        return self._stations.get(station_id)

    def all(self):
        return self._stations
