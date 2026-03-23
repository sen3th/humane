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

  async function submitVote(){
    if (!sessionId){
      status = "make a session first";
      return;
    }
    if (!voterId || !suspectId) {
      status = "enter voter and suspect ids";
      return;
    }
    try {
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/vote`,{
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          voter_id: voterId,
          suspect_id: suspectId,
        }),
      });
      const data=await res.json();
      if (!res.ok) {
        status = data.detail || "vote Failed";
        return;
      }
      status = "vote submitted";
    } catch (err) {
      status = "can't submit vote";
    }
  }

  async function revealResult(){
    if (!sessionId){
      status = "make a session first";
      return;
    }
    try{
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/reveal`);
      const data = await res.json();
      if (!res.ok) {
        status = data.detail || "reveal Failed";
        return;
    }
      revealData =  data;
      status = "Reveal ready";
    }catch (err) {
      status = "can't reveal result";
    }

  }

  function getPlayerNameById(id){
    const p = players.find((x) => x.player_id === id);
    return p ? p.name :id;
  }

  let sessionId ="";

  let playerName = "";
  let isBot = false;

  let messageText = "";
  let currentPlayerId = "";
  let players = [];
  
  let voterId = "";
  let suspectId = "";

  let revealData=null;
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

  <h3>Players rn:</h3>
  {#if players.length ===0}
    <p>No players yet</p>
    {:else}
    <ul>
      {#each players as p}
        <li on:click={()=> (voterId = p.player_id)} style="cursor: pointer;">
          {p.name} , id: {p.player_id} , bot: {p.is_bot}
        </li>
      {/each}
    </ul>
  {/if}
  <hr />
  <h3>Vote</h3>
  <input bind:value={voterId} placeholder="voter id"/>
  <input bind:value={suspectId} placeholder="suspect id"/>
  <button on:click={submitVote}>Submit Vote</button>
  <hr />
  <h3>Reveal</h3>
  <button on:click={revealResult}>Reveal Result</button>
  {#if revealData}
    <p>Human player was: {revealData.human_player
      ? `${revealData.human_player.name} (id: ${revealData.human_player.player_id})` : "none"}
    </p>
    <p>Most voted: {revealData.most_voted_id}</p>
    <h4>Vote tally</h4>
    {#if revealData && Object.keys(revealData.vote_tally || {}).length > 0}
      <ul>
        {#each Object.entries(revealData.vote_tally) as [playerId, count]}
         <li>{getPlayerNameById(playerId)}: {count}</li>
        {/each}
      </ul>
      {:else}
        <p>No votes</p>
      {/if}
  {/if}
  </main>