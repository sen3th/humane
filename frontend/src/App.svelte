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
    if (!humanName){
      status = "enter human player name first";
      return;
    }
    try {
      const res = await fetch("http://127.0.0.1:8000/sessions",{
        method : "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          human_name: humanName,
          bot_count: 3
        }),
      });
      const data = await res.json();
      if (!res.ok){
        status = data.detail || "cant create session";
        return;
      }
      sessionId = data.session_id;
      players = data.players || [];

      const human = players.find((p) => !p.is_bot);
      currentPlayerId = human ? human.player_id : "";
      if (botTickTimer) clearInterval(botTickTimer);
      botTickTimer = setInterval(botTick, 3000);

      if (phaseTimer) clearInterval(phaseTimer);
      phaseTimer = setInterval(loadGamesState, 1000);
      loadGamesState();

      status = `Session created . id ${sessionId}`;
      
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
      chatlog = [...chatlog, data];
      status = `${data.name} says: ${data.message}`;
      botTick();
      status = `${data.name} says: ${data.message}`;
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
      if (data.playerOutcome === "win"){
        alert("you win :), bots failed to vote you");
      } else if (data.playerOutcome === "lose"){
        alert("you lose, bots voted you out");
      } else{
        alert("nothing yet")
      }
      status = "Reveal ready";
    }catch (err) {
      status = "can't reveal result";
    }

  }

  async function botTick(){ 
    if (!sessionId) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/bot-tick`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok && data.ok && data.message){
        chatlog = [...chatlog, data.message];
      }
    } catch (err) {
    }
  }

  async function loadGamesState(){
    if (!sessionId) return;
    try{
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/state`);
      const data = await res.json();
      if (res.ok){
        gamePhase = data.phase;
        countdownSeconds = data.chat_seconds_left;
      }
    }catch (err) {
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
  let chatlog = [];

  let humanName = "";
  let botTickTimer = null;

  let gamePhase = "chat"
  let countdownSeconds = 0;
  let phaseTimer = null;
</script>

<main>
  <h1>Humane :)</h1>
  <button on:click={checkBackend}>Check Backend</button>
  <p>Phase: {gamePhase}, time Left: {countdownSeconds}</p>
  <p>Backend says: {status}</p>
  <p>Session ID: {sessionId}</p>
  <p>Current Player ID: {currentPlayerId}</p>
  <input bind:value={humanName} placeholder="enter your name"/>
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
  <button on:click={sendMessage} disabled={gamePhase !== "chat"}>Send Message</button>
  <h3>Chatlog</h3>
  {#if chatlog.length ===0}
    <p>no messages Yet</p>
    {:else}
      <ul>
        {#each chatlog as m}
          <li>{m.name}: {m.message}</li>
        {/each}
      </ul>
  {/if}

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
  <button on:click={submitVote} disabled={gamePhase !== "voting"}>Submit Vote</button>
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