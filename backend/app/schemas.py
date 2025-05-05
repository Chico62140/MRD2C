from pydantic import BaseModel

class RequestBase(BaseModel):
    name: str
    path: str
    filename: str
    description: str

class RequestCreate(RequestBase):
    pass

class Request(RequestBase):
    id: int
    status: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
