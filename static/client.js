let ws = null;
let room = null;
let name = null;
// track which players have already submitted a guess this round
let guessedPlayers = new Set();

function log(msg) {
  const el = document.getElementById('messages');
  const p = document.createElement('div');
  p.textContent = msg;
  el.appendChild(p);
  el.scrollTop = el.scrollHeight;
}

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

function updateState(data) {
  document.getElementById('category').textContent = data.category;
  document.getElementById('round').textContent = data.round;
  document.getElementById('tries').textContent = data.tries;
}

function updatePlayers(list) {
  document.getElementById('playerList').textContent = list.join(', ');
}

function updateGuessedPlayers(list) {
  document.getElementById('guessedList').textContent = list.join(', ');
}

function connect() {
  room = document.getElementById('room').value || 'room1';
  name = document.getElementById('name').value || 'Player';
  const numPlayers = parseInt(document.getElementById('numPlayers').value || '2');
  const tries = parseInt(document.getElementById('tries').value || '5');

  const protocol = (location.protocol === 'https:') ? 'wss' : 'ws';
  ws = new WebSocket(`${protocol}://${location.host}/ws/${room}`);

  ws.onopen = () => {
    setStatus('Connected');
    document.getElementById('game').style.display = 'block';
    // ensure inputs are enabled for a fresh round
    document.getElementById('guessInput').disabled = false;
    document.getElementById('sendGuessBtn').disabled = false;
    guessedPlayers.clear();
    updateGuessedPlayers([]);

    // send join message
    ws.send(JSON.stringify({type: 'join', payload: {name, numPlayers, tries}}));
    log('Joined room ' + room + ' as ' + name);
  };

  ws.onmessage = (ev) => {
    let msg = JSON.parse(ev.data);
    if (msg.type === 'state') {
      updateState(msg.payload);
      log('State updated');
    } else if (msg.type === 'players') {
      updatePlayers(msg.payload);
      log('Players: ' + msg.payload.join(', '));
    } else if (msg.type === 'guess_status') {
      // mark that the player (msg.player) has guessed this round
      guessedPlayers.add(msg.player);
      updateGuessedPlayers(Array.from(guessedPlayers));

      log(`Guess status (${msg.player}): ${msg.payload.message}`);

      // if this client submitted the guess, disable our input until next round/result
      if (msg.player === name) {
        document.getElementById('guessInput').disabled = true;
        document.getElementById('sendGuessBtn').disabled = true;
      }

    } else if (msg.type === 'check') {
      // A round evaluation has occurred
      log(`Round result: ${msg.payload.message}`);

      // Reset guessed trackers and re-enable inputs for next round
      guessedPlayers.clear();
      updateGuessedPlayers([]);
      document.getElementById('guessInput').disabled = false;
      document.getElementById('sendGuessBtn').disabled = false;

      // Update round/tries if the server sent them
      if (typeof msg.payload.round !== 'undefined') {
        document.getElementById('round').textContent = msg.payload.round;
        document.getElementById('tries').textContent = msg.payload.tries;
      }

    } else if (msg.type === 'error') {
      log('Error: ' + msg.payload.message);
    } else {
      log('Message: ' + JSON.stringify(msg));
    }
  };

  ws.onclose = () => {
    setStatus('Disconnected');
    document.getElementById('game').style.display = 'none';
  };

  ws.onerror = (e) => {
    log('WebSocket error');
  };
}

function sendGuess() {
  // guard: ensure connection and not disabled
  const input = document.getElementById('guessInput');
  const sendBtn = document.getElementById('sendGuessBtn');
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    log('Not connected');
    return;
  }
  if (input.disabled || sendBtn.disabled) return;

  const word = input.value.trim();
  if (!word) return;
  ws.send(JSON.stringify({type: 'guess', payload: {word}}));
  input.value = '';
  // optimistically disable input for this player until server acknowledges
  input.disabled = true;
  sendBtn.disabled = true;
}

document.getElementById('connectBtn').addEventListener('click', () => {
  connect();
});

document.getElementById('sendGuessBtn').addEventListener('click', () => {
  sendGuess();
});

// allow Enter to send guess
document.getElementById('guessInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendGuess();
});