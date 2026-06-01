// each player has a client.js instance, their own websocket connection
let ws = null;
let playerName = null;
// track which players have already submitted a guess this round
let guessedPlayers = new Set();

// all these helper functions change DOM to show up on the UI
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

function updateRoundGuesses(guesses) {
  const el = document.getElementById('roundGuesses');
  el.innerHTML = '';
  guesses.forEach(guess => {
    const p = document.createElement('p');
    p.textContent = guess;
    el.appendChild(p);
  });
}

function connect() {
  playerName = document.getElementById('name').value || 'Player';
  const roomName = document.getElementById('room').value || 'default';
  const numPlayers = parseInt(document.getElementById('numPlayers').value, 10) || 2;
  const tries = parseInt(document.getElementById('tries').value, 10) || 5;

  let protocol;
  if (location.protocol === 'https:') {
    protocol = 'wss';
  } else {
    protocol = 'ws';
  }

  ws = new WebSocket(`${protocol}://${location.host}/ws/${roomName}`);

  // defining a function to the onopen property of the websocket object (it will run, onopen), therefore doesn't need a name
  ws.onopen = function() {
    setStatus('Connected'); // will show up on the HTML now

    // hide playername up top and hide join form
    document.getElementById('joinDiv').style.display = 'none';
    document.getElementById('playerNameField').style.display = 'none'
    document.getElementById('playerNameDisplay').textContent = playerName;
    document.getElementById('playerNameDisplay').style.display = 'block';

    document.getElementById('game').style.display = 'block'; // block is default showing display
    // ensure inputs are enabled for a fresh round
    document.getElementById('guessInput').disabled = false;
    document.getElementById('sendGuessBtn').disabled = false;
    guessedPlayers.clear();
    updateGuessedPlayers([]);
    updateRoundGuesses([]); // clear guesses display

    // send join message, same format as sending a guess
    ws.send(JSON.stringify({type: 'join', payload: {name: playerName, numPlayers, tries}}));
    log('Joined as ' + playerName);
  };

  // this is when you receive a message from the server
  ws.onmessage = function(event) {
    let msg = JSON.parse(event.data);
    // each message has different states, so we know what to do with the payload
    if (msg.type === 'state') {
      updateState(msg.payload);
      log('State updated');
    } else if (msg.type === 'players') {
      updatePlayers(msg.payload);
      // log('Players: ' + msg.payload.join(', '));
    } else if (msg.type === 'guess_status') {
      // mark that the player (msg.player) has guessed this round
      guessedPlayers.add(msg.player);
      updateGuessedPlayers(Array.from(guessedPlayers));

      log(`Guess status (${msg.player}): ${msg.payload.message}`);

      // if this client submitted the guess, disable our input until next round/result
      if (msg.player === playerName) {
        document.getElementById('guessInput').disabled = true;
        document.getElementById('sendGuessBtn').disabled = true;
      }

    } else if (msg.type === 'check') {
      // a round evaluation has occurred — server has called check_answers()
      log(`Round result: ${msg.payload.message}`);

      // show each player's guess for this round
      updateRoundGuesses(msg.payload.guesses);

      // reset who-has-guessed tracker regardless of outcome
      guessedPlayers.clear();
      updateGuessedPlayers([]);

      if (msg.payload.status === 'success' || msg.payload.status === 'L') {
        // game is over — lock inputs so no more guesses can be submitted
        document.getElementById('guessInput').disabled = true;
        document.getElementById('sendGuessBtn').disabled = true;
        setStatus('Game over — ' + msg.payload.message);
      } else {
        // still going — re-enable inputs for next round
        document.getElementById('guessInput').disabled = false;
        document.getElementById('sendGuessBtn').disabled = false;
        // update round/tries counter if server sent them
        if (typeof msg.payload.round !== 'undefined') {
          document.getElementById('round').textContent = msg.payload.round;
          document.getElementById('tries').textContent = msg.payload.tries;
        }
      }

    } else if (msg.type === 'error') {
      log('Error: ' + msg.payload.message);
    // emergency backup?
    } else {
      log('Message: ' + JSON.stringify(msg));
    }
  };

  ws.onclose = function() {
    setStatus('Disconnected');
    document.getElementById('game').style.display = 'none';
  };

  ws.onerror = function() {
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
  if (input.disabled || sendBtn.disabled) {
    log('Input disabled');
    return;
  }

  const word = input.value.trim(); // trim removes whitespace
  if (!word) return;
  // same format when sending guess and connect
  ws.send(JSON.stringify({type: 'guess', payload: {word}}));
  // clear input
  input.value = '';
  // optimistically disable input for this player until server acknowledges
  input.disabled = true;
  sendBtn.disabled = true;
}

// form submit for join
document.getElementById('joinForm')
  .addEventListener('submit', function (event) {
    event.preventDefault();
    connect();
  });

// same for send guess btn
document.getElementById('sendGuessBtn')
  .addEventListener('click', function () {
    sendGuess()
  });

// allows enter to send guess
document.getElementById('guessInput')
  .addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      sendGuess();
    }
  });