# Dial Nomo
Run the following to connect the agent to your room.
```
python3 agents.py connect --room="<room_nam>"
```

To start the server
```
python3 server.py
```

With the server started, you can make the following requests

```
# Create SIP Participant
curl -X POST http://localhost:8000/create_sip_participant \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+15197229687",
    "room_name": "my-sip-room",
    "participant_identity": "sip-human-agent",
    "participant_name": "Human Agent",
    "krisp_enabled": true
  }'

# Create Room
curl -X POST http://localhost:8000/create_room \
  -H "Content-Type: application/json" \
  -d '{"room_name": "my-new-room"}'

# Join Room
curl -X POST http://localhost:8000/join_room \
  -H "Content-Type: application/json" \
  -d '{"identity": "user123", "roomName": "my-room"}'
```
