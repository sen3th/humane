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
      playerName = "";
      status = `${data.name} joined`;
    }catch (err) {
      status = "can't join session";
    }
  }

  let sessionId ="";

  let playerName = "";
  let isBot = false;
</script>

<main>
  <h1>Humane :)</h1>
  <button on:click={checkBackend}>Check Backend</button>
  <p>Backend says: {status}</p>
  <p>Session ID: {sessionId}</p>
  <button on:click={createSession}>make Session</button>
  <input bind:value={playerName} placeholder="Player Name" />
  <label>
    <input type="checkbox" bind:checked={isBot} />
    Is Bot
  </label>
  <button on:click={joinPlayer}>Join</button>
</main>