from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict

class LoginRequest(BaseModel):
    name: str = None
    email: EmailStr
    role: str = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# anything
