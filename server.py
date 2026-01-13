from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from game import Game
from main import DEFAULT_CATEGORIES

app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

class ConnectionManager:
    def __init__(self):
        # room -> list of WebSocket
        self.rooms = {}
        # room -> { websocket: player_name }
        self.room_players = {}
        # room -> Game
        self.games = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.rooms.setdefault(room, []).append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)
        if room in self.room_players and websocket in self.room_players[room]:
            del self.room_players[room][websocket]

        # cleanup empty room
        if room in self.rooms and len(self.rooms[room]) == 0:
            self.rooms.pop(room, None)
            self.room_players.pop(room, None)
            self.games.pop(room, None)

    def set_player(self, websocket: WebSocket, room: str, name: str):
        self.room_players.setdefault(room, {})[websocket] = name

    def players_list(self, room: str):
        return list(self.room_players.get(room, {}).values())

    async def broadcast(self, room: str, message: dict):
        conns = list(self.rooms.get(room, []))
        for conn in conns:
            try:
                await conn.send_json(message)
            except Exception:
                # ignore send failures; disconnect will cleanup later
                pass

manager = ConnectionManager()

@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "join":
                name = payload.get("name", "Anon")
                numPlayers = int(payload.get("numPlayers", 2))
                tries = int(payload.get("tries", 5))
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
                word = payload.get("word", "")
                game = manager.games.get(room)
                if not game:
                    await websocket.send_json({"type":"error","payload":{"message":"No game in room. Join first."}})
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
