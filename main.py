from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tortoise.contrib.fastapi import register_tortoise
from tortoise.transactions import in_transaction
from pydantic import BaseModel, validator
from tortoise import Tortoise
from models import User, Role, PatientInfo
import jwt
from typing import Dict
from passlib.context import CryptContext
from tortoise.contrib.pydantic import pydantic_model_creator

app = FastAPI()

user_pydantic = pydantic_model_creator(User)
role_pydantic = pydantic_model_creator(Role)
patient_info_pydantic = pydantic_model_creator(PatientInfo)


# Secret key for JWT
SECRET_KEY = "your-secret-key"

# HTTP Bearer token authentication
security = HTTPBearer()
websocket_connections: Dict[str, WebSocket] = {}


# Create an instance of the CryptContext class for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Function to retrieve the current user based on JWT token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    username = verify_token(credentials)
    # Assuming you have a User model with a method to retrieve the user by username
    user = User.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Function to generate JWT token
def create_jwt_token(username: str):
    payload = {"sub": username}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# User registration request model
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

    # Validator to check if role is valid
    @validator('role')
    def validate_role(cls, role):
        valid_roles = ["secretary", "patient", "doctor"]
        if role.lower() not in valid_roles:
            raise ValueError("Invalid role type, only (secretary, patient, doctor) are allowed")
        return role.lower()


# User authentication request model
class UserAuthenticate(BaseModel):
    username: str
    password: str

# Patient information request model
class PatientInfoCreate(BaseModel):
    patient_id: int
    info: str

# User response model
class UserResponse(BaseModel):
    username: str
    role: str

# Route to get information about the currently authenticated user
@app.get("/auth/me", response_model=User)
async def get_current_user(user: User = Depends(verify_token)):
    await User.get_or_none(User.username == user["sub"])
    return user_pydantic(user)

# User registration route
@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    async with in_transaction():
        # Check if the username already exists
        if await User.filter(username=user_data.username).exists():
            raise HTTPException(status_code=400, detail="Username already exists")
        # Get the role object
        role_found = await Role.get_or_create(user_data.role.lower())
        print(role_found)
        if not role_found:
            raise HTTPException(status_code=400, detail="Invalid role type")

        hashed_password = pwd_context.hash(user_data.password)
        # Create the user
        user = await User.create(username=user_data.username, password_hash=hashed_password, role=role_found)

    return UserResponse(username=user.username, role=user_pydantic(user).role)

# User authentication route
@app.post("/login")
async def login(user_data: UserAuthenticate):
    user = await User.get_or_none(username=user_data.username)
    if not user or user.password_hash != user_data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate JWT token
    token = create_jwt_token(user.username)

    return {"access_token": token}

# Route to send patient information to authenticated doctors using WebSocket
@app.post("/patients/{patient_id}/send_info")
async def send_patient_info(
    patient_id: int,
    info: str,
    current_user: User = Depends(verify_token)
):
    # Check if the current user is a doctor
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can send patient information")

    # Retrieve the patient information from the database
    patient = await PatientInfo.get_or_none(id=patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient information not found")

    # Construct the message to be sent
    message = f"Patient ID: {patient_id}\nInfo: {info}"

    # Send the message to all connected doctors using WebSocket
    for connected_username, connected_websocket in websocket_connections.items():
        if connected_username != current_user.username:
            await connected_websocket.send_text(message)

    return {"message": "Patient information sent successfully to other doctors"}

# WebSocket route for real-time communication
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, current_user: User = Depends(verify_token)):
    # Check if the current user is a doctor
    if current_user.role != "doctor":
        await websocket.close()
        return
    
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Add the WebSocket connection to the dictionary
    websocket_connections[username] = websocket

    try:
        while True:
            # Receive data from the client
            data = await websocket.receive_text()

            # Broadcast the received data to all connected doctors except the sender
            for connected_username, connected_websocket in websocket_connections.items():
                if connected_username != username:
                    await connected_websocket.send_text(data)
    except WebSocketDisconnect:
        # Remove the WebSocket connection from the dictionary when disconnected
        del websocket_connections[username]

register_tortoise(
    app,
    db_url='sqlite://:memory:',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True,
)
@app.on_event("startup")
async def startup_event():
    await create_default_roles()

async def create_default_roles():
    # Check if roles exist in the database
    for role_type in ["secretary", "doctor", "laboratory"]:
        role = await Role.get_or_none(type=role_type)
        if not role:
            # If the role doesn't exist, create it
            await Role.create(type=role_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
