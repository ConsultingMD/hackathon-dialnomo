import asyncio
from dotenv import load_dotenv
from livekit import api
import os
from livekit.protocol.sip import CreateSIPParticipantRequest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, Field

load_dotenv(dotenv_path=".env.local")

class LiveKitServer:
    def __init__(self):
        self.app = FastAPI()
        self.allowed_origins = [
            "http://localhost:10055"
        ]
        self._setup_middlewares()
        self._setup_routes()

    def _setup_middlewares(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        # Request models
        class CreateSIPParticipantData(BaseModel):
            phone_number: str
            room_name: str
            participant_identity: str
            participant_name: str

        class CreateRoomData(BaseModel):
            room_name: str

        class JoinRoomData(BaseModel):
            identity: str
            room_name: str = Field(..., alias="roomName")

        @self.app.post("/create_sip_participant")
        async def create_sip_participant(data: CreateSIPParticipantData):
            """Endpoint to create a SIP participant with JSON parameters"""
            livekit_api = api.LiveKitAPI()
            request = CreateSIPParticipantRequest(
                sip_trunk_id="ST_Cin8hUGkqncP",
                sip_call_to=data.phone_number,
                room_name=data.room_name,
                participant_identity=data.participant_identity,
                participant_name=data.participant_name,
                krisp_enabled=True
            )
            participant = await livekit_api.sip.create_sip_participant(request)
            await livekit_api.aclose()
            return {"message": f"Successfully created {participant}"}

        @self.app.post("/create_room")
        async def create_room(data: CreateRoomData):
            """Endpoint to create a new room with JSON parameters"""
            livekit_api = api.LiveKitAPI()
            request = api.CreateRoomRequest(
                name=data.room_name,
                empty_timeout=300,
                max_participants=10,
                metadata="{}",
                egress=None,
                min_playout_delay=0,
                max_playout_delay=0,
                sync_streams=False
            )
            room = await livekit_api.room.create_room(request)
            await livekit_api.aclose()
            return {"message": f"Successfully created room {room.name}"}

        @self.app.post("/join_room")
        async def join_room(data: JoinRoomData):
            """Endpoint to generate a join token with JSON parameters"""
            livekit_api = api.LiveKitAPI()
            token = (
                api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
                .with_identity(data.identity)
                .with_name("my name")
                .with_grants(api.VideoGrants(room_join=True, room=data.room_name))
			)
            token_value = token.to_jwt()
            await livekit_api.aclose()
            return {"token": token_value}

        @self.app.post("/agent_join")
        async def agent_join(data: CreateRoomData):
            """Endpoint to execute the agent script"""
            process = await asyncio.create_subprocess_exec(
                "python", "agents.py", "connect", f"--room={data.room_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return {"message": "Agent script executed successfully", "output": stdout.decode()}
            return {"message": "Agent script execution failed", "error": stderr.decode()}

        @self.app.post("/kick_participant")
        async def kick_participant(data: JoinRoomData):
            """Endpoint to kick a participant by their identity"""
            livekit_api = api.LiveKitAPI()
            request = api.RoomParticipantIdentity(
                room=data.room_name,
                identity=data.identity
            )
            await livekit_api.room.remove_participant(request)
            await livekit_api.aclose()
            return {"message": f"Successfully kicked participant {data.identity} from room {data.room_name}"}

def run_server():
    server = LiveKitServer()
    uvicorn.run(server.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()
