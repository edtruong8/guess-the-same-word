from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from game import Game, DEFAULT_CATEGORIES

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/client.js")
async def serve_client_js():
    return FileResponse("static/client.js")

# NOTE: async allows multiple connections to be handled concurrently, without waiting for each to finish or blocking server
# NOTE: await - pause while waiting, allow other connections to run

class ConnectionManager:
    def __init__(self):
        # list of websockets, so we can broadcast messages to the correct room
        self.rooms = {}
        # {websocket: player_name}, can update player list to show name, and can use name for broadcasts
        self.room_players = {}
        # stores game objects per room
        self.games = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        # add this websocket connection to the room dict
        self.rooms.setdefault(room, []).append(websocket) # setdefault cause room isn't a key yet, can 2 line if u want

    def disconnect(self, websocket: WebSocket, room: str):
        # remove websocket from room list
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)
        # remove socket from player mapping (player isn't in room, and can update list)
        if room in self.room_players and websocket in self.room_players[room]:
            del self.room_players[room][websocket]

        # cleanup empty room
        if room in self.rooms and len(self.rooms[room]) == 0:
            self.rooms.pop(room, None)
            self.room_players.pop(room, None)
            self.games.pop(room, None)

    # websocket : player name
    def set_player(self, websocket: WebSocket, room: str, name: str):
        self.room_players.setdefault(room, {})[websocket] = name

    def players_list(self, room: str):
        return list(self.room_players.get(room, {}).values())

    async def broadcast(self, room: str, message: dict):
        connections = list(self.rooms.get(room, []))
        for conn in connections:
            try:
                # this is the ws.onmessage in JS, it outputs this
                await conn.send_json(message)
            except Exception:
                # ignore send failures; disconnect will cleanup later
                pass

# one global manager for all websockets
manager = ConnectionManager()

# when a client opens a websocket, run this func (single room: "default")
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    room = room_id
    # client connects, but not yet joined a game
    await manager.connect(websocket, room)
    try:
        # forever in loop to receive messages from this client
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload")

            if msg_type == "join":
                name = payload.get("name")
                numPlayers = int(payload.get("numPlayers"))
                tries = int(payload.get("tries"))
                manager.set_player(websocket, room, name)

                # initialize a Game for the room on first join
                if room not in manager.games:
                    categories = DEFAULT_CATEGORIES.copy()
                    manager.games[room] = Game(categories=categories, tries=tries, numPlayers=numPlayers)

                game = manager.games[room]
                # inform all clients about current players and state
                await manager.broadcast(room, {"type":"players", "payload": manager.players_list(room)})
                await manager.broadcast(room, {"type":"state", "payload": {"category":game.category, "round":game.round, "tries":game.tries}})

            elif msg_type == "guess":
                word = payload.get("word")
                game = manager.games.get(room)
                # if u try guessing before joining
                if not game:
                    await websocket.send_json({"type":"error","payload":{"message":"Join a game first."}})
                    continue

                res = game.submit_guess(word)
                # announce guess status
                await manager.broadcast(room, {"type":"guess_status", "payload": res, "player": manager.room_players.get(room, {}).get(websocket)})

                # when all players have guessed, evaluate
                if len(game.guesses) == game.numPlayers:
                    check = game.check_answers()
                    await manager.broadcast(room, {"type":"check", "payload": check})
                    
            elif msg_type == "state":
                game = manager.games.get(room)
                if game:
                    await websocket.send_json({"type":"state","payload":{"category":game.category,"round":game.round,"tries":game.tries}})

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        # notify remaining players
        if room in manager.rooms:
            await manager.broadcast(room, {"type":"players", "payload": manager.players_list(room)})
