<script>
  let status = "Not checked yet";

  async function checkBackend() {
    try {
      const res = await fetch("http://127.0.0.1:8000/ping");
      const data = await res.json();
      status = data.message;
    } catch (err) {
      status = "cannot reach backend";
    }
  }

  async function createSession() {
    try {
      const res = await fetch("http://127.0.0.1:8000/sessions",{
        method : "POST",
      });
      const data = await res.json();
      sessionId = data.session_id;
      
    }catch (err) {
      sessionId = "can't create session";
    }
    
  }

  async function joinPlayer(){
    if (!sessionId) {
      alert("make a session first");
      return;
    }
    if (!playerName) {
      alert("enter player name");
      return;
    }
    try{
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/join`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: playerName,
          is_bot: isBot,
        }),
      });
      const data = await res.json();
      currentPlayerId = data.player_id;
      playerName = "";
      players = [...players, data];
      status = `${data.name} joined id ${data.player_id}`;
    }catch (err) {
      status = "can't join session";
    }
  }

  async function sendMessage() {
    if (!sessionId) {
      status = "make a session first";
      return;
    }
    if (!currentPlayerId){
      status = "enter player id";
      return;
    }
    if (!messageText) {
      status = "enter a message";
      return;
    }
    try {
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/chat`, {
        method:"POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          player_id: currentPlayerId,
          message: messageText,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        status=data.detail || "chat Failed";
        return;
      }
      status = `${data.name} says: ${data.message}`;
      messageText = "";
    } catch (err) {
      status = "can't send message";
    }
  }

  let sessionId ="";

  let playerName = "";
  let isBot = false;

  let messageText = "";
  let currentPlayerId = "";
  let players = [];
</script>

<main>
  <h1>Humane :)</h1>
  <button on:click={checkBackend}>Check Backend</button>
  <p>Backend says: {status}</p>
  <p>Session ID: {sessionId}</p>
  <p>Current Player ID: {currentPlayerId}</p>
  <button on:click={createSession}>make Session</button>
  <input bind:value={playerName} placeholder="Player Name" />
  <label>
    <input type="checkbox" bind:checked={isBot} />
    Is Bot
  </label>
  <button on:click={joinPlayer}>Join</button>
  <hr />
  <input bind:value={currentPlayerId} placeholder="player id" />
  <input bind:value={messageText} placeholder="type a message" />
  <button on:click={sendMessage}>Send Message</button>
</main>