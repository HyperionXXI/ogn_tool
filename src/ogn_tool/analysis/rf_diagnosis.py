class RFDiagnosis:
    """
    Basic RF diagnostic container used by RFAnalysisEngine.
    """

    def __init__(self, directional_balance=None, blind_zones=None):
        self.directional_balance = directional_balance
        self.blind_zones = blind_zones

    def to_dict(self):
        return {
            "directional_balance": self.directional_balance,
            "blind_zones": self.blind_zones,
        }
