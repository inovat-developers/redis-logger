from pydantic import BaseModel

__all__ = [
    "SRedisLogger",
]


class SRedisLogger(BaseModel):
    name: str
    # TODO add host, port config to redis connection
