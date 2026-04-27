from taskweave.dialect import Classifier, RExtractor, Field, OutputType
from taskweave.dialect import FieldSchema, JsonSchemaType, PersistStrategy, PersistPolicy
from taskweave import FileBackend
from taskweave.context import constants
from taskweave.workers import ClassifyingProducer
from taskweave.tasks import Task, LocalProcessStrategy

# Declare fields
frame   = FieldSchema("frame",  JsonSchemaType.INT)
fps     = FieldSchema("fps",    JsonSchemaType.FLOAT)
time    = FieldSchema("time",   JsonSchemaType.FLOAT)
speed   = FieldSchema("speed",  JsonSchemaType.FLOAT)

# Build a parser from field 

progress_parser = RExtractor(
    extractors=[
        # TODO: keyword and separator disapear in profit of target : str | Pattern
        # TODO :field becomes schema
        # TODO: FieldExtractor becomes Field
        Field(schema=frame, keyword="frame", separator="="),
        Field(schema=fps,   keyword="fps",   separator="="),
        Field(schema=time,  keyword="time",  separator="="),
        Field(schema=speed, keyword="speed", separator="="),
    ]
)

# TODO: change comment for "Classify : each line is parsed according to cascading rules, fisrt match wins"
# Classify lines — first match wins
ffmpeg_classifier = Classifier(
    rules={
        progress_parser: OutputType.PROGRESS,
    },
    persist=PersistStrategy(
        backend=FileBackend(log_dir=constants.log_folder),
        # TODO: added field on dataclass persist : list[RegexFieldParser]
        policy=PersistPolicy.DISCARDED_ONLY,
    )
)

task = Task(
    name="ffmpeg_extract",
    strategy=LocalProcessStrategy(),
    command=["ffmpeg", "-i", "input.mp4", ...],
    producer=ClassifyingProducer(classifier=ffmpeg_classifier),
)