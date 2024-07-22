from typing import Annotated, reveal_type
import uuid
import logging

from fastapi_events.dispatcher import dispatch

from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event
from enum import Enum
from datetime import datetime

from pydantic import BaseModel
from fastapi_events.registry.payload_schema import registry as payload_schema
from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(EventHandlerASGIMiddleware, handlers=[local_handler])


class UserEvents(Enum):
    SIGNED_UP = "USER_SIGNED_UP"
    ACTIVATED = "USER_ACTIVATED"


# Registering your event payload schema
@payload_schema.register(event_name=UserEvents.SIGNED_UP)
class SignUpPayload(BaseModel):
    user_id: uuid.UUID
    created_at: datetime


# which is also equivalent to
# class SignUpPayload(BaseModel):
#     __event_name__ = "USER_SIGNED_UP"
#
#     user_id: uuid.UUID
#     created_at: datetime


type Payload[T] = Annotated[T, BaseModel]


@local_handler.register(event_name=UserEvents.SIGNED_UP)
def handle_all_user_events(event: Event):
    event_name = event[0]
    payload: Payload[SignUpPayload] = event[1]
    payload.foo

    reveal_type(payload)
    print(f"type: {type(payload)}")
    # get the attributes of payload, which is a pydantic model
    attrs = payload.__fields__.keys()
    # now let's get their types
    for attr in attrs:
        print(f"type of {attr}: {type(getattr(payload, attr))}")

    print(f"payload: {payload.user_id}")
    print(f"Received event: {event_name} with payload: {payload}")


@app.get("/trigger_event")
def trigger_event():
    user_id = uuid.uuid4()
    timestamp = datetime.now()
    dispatch(UserEvents.SIGNED_UP, SignUpPayload(user_id=user_id, created_at=timestamp))
    return {"msg": "Event triggered"}


# Example request to make sure everything is defined properly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=uvicorn.config.LOGGING_CONFIG,
        reload=True,
    )
