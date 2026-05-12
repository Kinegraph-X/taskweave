from .command_schema import CommandSchema
from .command_serializer import CommandSerializer

from taskweave_transport import ControlTransport

class ControlDialect:
    """ Describes what a process can receive."""
    commands: list[CommandSchema]
    transport: ControlTransport
    serializer: CommandSerializer  # comment encoder CommandSchema → bytes

"""
fetch_control = ControlDialect(
    commands=[pause_command, seek_command],
    transport=StdinTransport,   # résolu au runtime par SessionManager
    serializer=LineSerializer(),
)

task = Task(
    strategy=LocalProcessStrategy(cmd=["python", "fetcher.py"]),
    log_producer=ClassifyingProducer(classifier=fetch_classifier),
    control=fetch_control,  # nouveau champ, nullable pour l'instant
)
"""