from taskweave_protocol import ControlDialect
from taskweave_transport import ControlTransport

class ControlChannel:
    def __init__(
        self,
        dialect: ControlDialect,
        transport: ControlTransport,  # reçoit StdinTransport injecté
    ):...