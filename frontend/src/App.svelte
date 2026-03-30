<script>
  import Swal from "sweetalert2";

  let status = "Not checked yet";
  const APP_STATE_KEY = "humane_state";

  async function checkBackend() {
    try {
      const res = await fetch("https://humane-1-dznm.onrender.com/ping");
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
    clearUiState();
    try {
      const res = await fetch("https://humane-1-dznm.onrender.com/sessions",{
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
        saveUiState();
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
      const res = await fetch(`https://humane-1-dznm.onrender.com/sessions/${sessionId}/chat`, {
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
      saveUiState();
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
    if (!currentPlayerId){
      status = "no player id found"
      return;
    }
    if (!suspectId){
      status = "Pick a suspect fist!"
      return;
    }
    try {
      const res = await fetch(`https://humane-1-dznm.onrender.com/sessions/${sessionId}/vote`,{
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          voter_id: currentPlayerId,
          suspect_id: suspectId,
        }),
      });
      const data=await res.json();
      if (!res.ok) {
        status = data.detail || "vote Failed";
        return;
      }
      status = "vote submitted";
      suspectId = "";
      saveUiState();
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
      const res = await fetch(`https://humane-1-dznm.onrender.com/sessions/${sessionId}/reveal`);
      const data = await res.json();
      if (!res.ok) {
        status = data.detail || "reveal Failed";
        return;
    }
      revealData =  data;
      await showOutcomeAlert(data.playerOutcome);
      status = "Reveal ready";
      saveUiState();
    }catch (err) {
      status = "can't reveal result";
    }

  }

  async function botTick(){
    if (!sessionId) return;
    try {
      const res = await fetch(`https://humane-1-dznm.onrender.com/sessions/${sessionId}/bot-tick`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok && data.ok && data.message){
        chatlog = [...chatlog, data.message];
        saveUiState();
      }
    } catch (err) {
    }
  }

  async function loadGamesState(){
    if (!sessionId) return;
    try{
      const res = await fetch(`https://humane-1-dznm.onrender.com/sessions/${sessionId}/state`);
      const data = await res.json();
      if (res.ok){
        gamePhase = data.phase;
        countdownSeconds = data.chat_seconds_left;
        saveUiState();
      }
    }catch (err) {
    }
    
  }

  async function showOutcomeAlert(playerOutcome){
    if (playerOutcome === "win"){
      await Swal.fire({
        title: "You Win :)",
        text: "bots failed to vote you",
        icon: "success",
        confirmButtonText: "yay!",
        confirmButtonColor: "#4ade80"
      })
      return;
    }
    if (playerOutcome === "lose"){
      await Swal.fire({
        title: "You Lose!",
        text: "bots voted you out",
        icon: "error",
        confirmButtonText: "ok",
        confirmButtonColor: "#ef4444"
      })
      return;
    }
  }
  
  function getPlayerNameById(id){
    const p = players.find((x) => x.player_id === id);
    return p ? p.name: id;
  }

  function saveUiState(){
    const data = {
      sessionId,
      currentPlayerId,
      humanName,
      players,
      chatlog,
      gamePhase,
      countdownSeconds,
      suspectId,
      revealData
    };
    localStorage.setItem(APP_STATE_KEY, JSON.stringify(data));
  }

  function restoreUiState(){
    const raw = localStorage.getItem(APP_STATE_KEY);
    if (!raw) return;
    try {
      const data = JSON.parse(raw);
      sessionId = data.sessionId || "";
      currentPlayerId = data.currentPlayerId || "";
      humanName = data.humanName || "";
      players = data.players || [];
      chatlog = data.chatlog || [];
      gamePhase = data.gamePhase || "chat";
      countdownSeconds = data.countdownSeconds || 0;
      suspectId = data.suspectId || "";
      revealData = data.revealData || null;
    } catch (err) {
      localStorage.removeItem(APP_STATE_KEY);
    }
  }

  function clearUiState(){
    localStorage.removeItem(APP_STATE_KEY);
  }

  function resetGame(){
    clearUiState();
    sessionId ="";
    currentPlayerId = "";
    players = [];
    chatlog = [];
    gamePhase = "chat";
    countdownSeconds = 0;
    suspectId = "";
    revealData = null;
    messageText = "";
  }

  function showInstructions(){
    Swal.fire({
      title: "How to play",
      html:`
      <ul class="text-left list-disc pl-5">
        <li>Enter your name and create a session</li>
        <li>Chat with bots till the timer runs out (try to blend in!)</li>
        <li>After voting phase starts, sabotage bots by voting for them (or yourself if you're crazy) </li>
        <li>After voting ends, click reveal to see if you fooled the bots or not</li>
        <li>Make a new session to play again :)</li>
      </ul>
      `
    })
  }

  showInstructions();

  let sessionId ="";

  let messageText = "";
  let players = [];

  let revealData=null;
  let chatlog = [];

  let humanName = "";
  let botTickTimer = null;

  let gamePhase = "chat"
  let countdownSeconds = 0;
  let phaseTimer = null;

  let currentPlayerId = "";
  let suspectId = "";

  restoreUiState();
  if (sessionId){
    if (botTickTimer) clearInterval(botTickTimer);
    botTickTimer = setInterval(botTick, 3000);

    if (phaseTimer) clearInterval(phaseTimer);
    phaseTimer = setInterval(loadGamesState, 1000);
    loadGamesState();
  }
</script>

<main class="min-h-screen w-full px-3 py-6 sm:px-6">
<div class="mx-auto w-full max-w-3xl space-y-4">
  <h1 class="text-lg mt-2.5">Humane :)</h1>
  <br>

  <div class="w-full rounded-xl bg-gray-200 p-4 shadow-sm">
    <p class="text-lg">Phase: {gamePhase}</p>
    <p class="text-lg">Time left: {countdownSeconds}</p>
    <br>
    <button on:click={resetGame} class="bg-blue-500 text-white px-4 py-2 rounded">New Game</button>
    <br/>
    <br/>
    <input bind:value={humanName} placeholder="enter your name" class="border border-gray-300 p-2 rounded"/>
    <button on:click={createSession} class="bg-green-500 text-white px-4 py-2 rounded">make Session</button>
    <br/>
    <br/>
  </div>
  <br>

<div class="w-full rounded-xl bg-gray-200 p-4 shadow-sm">
  <h3 class="font-bold">Chatlog</h3>
  <br>
  {#if chatlog.length ===0}
    <p>No messages Yet!</p>
    {:else}
    <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;">
      <ul>
        {#each chatlog as m}
          <li>{m.name}: {m.message}</li>
        {/each}
      </ul>
    </div>
  {/if}
    <br>
  <input bind:value={messageText} placeholder="type a message" class="border border-gray-300 p-2 rounded"/>
  <button on:click={sendMessage} disabled={gamePhase !== "chat"} class="bg-blue-500 text-white px-4 py-2 rounded">Send Message</button>
</div>
  
  <br>


<div class="w-full rounded-xl bg-gray-200 p-4 shadow-sm">
  <h3 class="font-bold">Current Players:</h3>
  {#if players.length ===0}
    <p>No players yet!</p>
    {:else}
    <ul>
      {#each players as p}
        <li>
         <button type="button" on:click={()=> {suspectId = p.player_id; saveUiState(); }} style="cursor: pointer;">
          {p.name} , id: {p.player_id} , bot: {p.is_bot}
         </button>
        </li>
      {/each}
    </ul>
  {/if}
  </div>
  <br>

  <div class="w-full rounded-xl bg-gray-200 p-4 shadow-sm">
  <h3 class="font-bold">Vote</h3>
  <br>
  <p>selected Suspect: {suspectId? getPlayerNameById(suspectId) : "none"}</p>
  <br>
  <button on:click={submitVote} disabled={gamePhase !== "voting"} class="font-bold text-white bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded">Submit Vote</button>
  </div>
  <br>

  <div class="w-full rounded-xl bg-gray-200 p-4 shadow-sm">
  <button on:click={revealResult} class="font-bold text-white bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded">Reveal Result</button>
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
  </div>
</div>
  </main>

<footer class="w-full py-4 text-center text-sm text-gray-500">
  &copy; <a href="https://seneth.me" target="_blank" rel="noopener noreferrer">seneth.me</a> | <a href="https://github.com/sen3th/humane" target="_blank" rel="noopener noreferrer">GitHub</a>
</footer>