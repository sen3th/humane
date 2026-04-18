<script>
  import Swal from "sweetalert2";

  let status = "Not checked yet";
  const APP_STATE_KEY = "humane_state";

  const CHAT_HISTORY_KEY = "humane_chat_history";
  const HISTORY_LIMIT = 50;
  let sessionHistory = [];

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
    if (!Number.isFinite(Number(gameDurationSeconds))){
      status = "invalid time"
      return;
    }
    gameDurationSeconds = Math.max(15, Math.min(600, Number(gameDurationSeconds)));

    if (botTickTimer) {clearInterval(botTickTimer); botTickTimer = null;}
    if (phaseTimer){clearInterval(phaseTimer); phaseTimer = null;}
    sessionId="";
    currentPlayerId = "";
    players = [];
    chatlog = [];
    messageText = "";
    gamePhase = "";
    countdownSeconds = 0;
    suspectId = "";
    revealData = null;
    voteTally={};
    voteCounts = {};
    hasVoted = false;
    alreadyRevealed = false;
    currentTopic = "";
    
    clearUiState();
    try {
      const ready = await waitForBackendWake();
      if (!ready){
        status = "try again later";
        isBackendStarting = false;
        return;
      }
      const res = await fetch("https://humane-1-dznm.onrender.com/sessions",{
        method : "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          human_name: humanName,
          bot_count: 3,
          chat_duration_seconds: gameDurationSeconds,
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
      currentTopic = data.topic || "";

      humanName ="";

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
    } finally{
      isBackendStarting =false;
      wakeMessage = "";
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
    if (!messageText.trim()) {
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
          message: messageText.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        status=data.detail || "chat Failed";
        return;
      }
      chatlog = [...chatlog, data];
      messageText = ""
      status = `${data.name} says: ${data.message}`;
      saveUiState();
      status = `${data.name} says: ${data.message}`;
    } catch (err) {
      status = "can't send message";
    }
  }

  function handleMessageKeydown(event){
    if (event.key === "Enter"){
      event.preventDefault();
      sendMessage();
    }
  }

  async function submitVote(){
    if (hasVoted){
      status = "You already voted";
      return;
    }
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
      hasVoted = true;
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
      revealData = data;
      appendSessionHistoryOnce(data);
      recordStatsFromReveal(data);
      saveUiState();
      await showOutcomeAlert(getPlayerOutcome(data));
      status = "Reveal ready";
      alreadyRevealed = true;
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
        currentTopic = data.topic || currentTopic;
        const parsedSeconds = Number(data.chat_seconds_left ?? data.seconds_left ?? 0);
        countdownSeconds = Number.isFinite(parsedSeconds) ? Math.max(0, Math.floor(parsedSeconds)) : 0;
        voteTally = data.vote_tally || {};
        voteCounts = data.vote_counts || {};
        saveUiState();

        if (gamePhase === "reveal" && !revealData && data.reveal_data){
          revealData = data.reveal_data;
          appendSessionHistoryOnce(revealData);
          recordStatsFromReveal(revealData);
          await showOutcomeAlert(getPlayerOutcome(revealData));
          status = "Reveal ready";
          saveUiState();
        }
      }
    }catch (err) {
      console.error("can't load game state", err);
    }
  }

  async function waitForBackendWake(maxWaitMs = 90000, pollEveryMs =2000){
    isBackendStarting = true;
    wakeStarted = Date.now();
    wakeMessage = "starting the backend rn...";

    while (Date.now() - wakeStarted < maxWaitMs){
      try{
        const res=await fetch("https://humane-1-dznm.onrender.com/ping",{
          method: "GET",
          cache: "no-store"
        });
        if (res.ok){
          wakeMessage = "backend ready. starting session..";
          return true;
        }
      } catch(_){}
      const elapsed = Math.floor((Date.now() - wakeStarted)/1000);
      wakeMessage = `waking backend... ${elapsed}s`;
      await new Promise((r)=> setTimeout(r, pollEveryMs));
    }
    wakeMessage = "time out, try again";
    return false;

  }

  function clearSessionHistory(){
    sessionHistory = [];
    localStorage.removeItem(CHAT_HISTORY_KEY);
  }

  function tallyText(){
    const lines = Object.entries(voteCounts).map(
      ([id, count]) => `${getPlayerNameById(id)}:${count}`
  ); return lines.length?`Vote tally:\n${lines.join("\n")}\n\n`:"";
  }
  function getPlayerOutcome(data) {
    return data?.playerOutcome ?? data?.player_outcome ?? data?.revealOutcome ?? data?.reveal_outcome ?? "";
  }

  function buildSessionHistory(revealPayload){
    const outcome = getPlayerOutcome(revealPayload);
    return {
      id: `${sessionId}-${Date.now()}`,
      createdAt: new Date().toISOString(),
      sessionId,
      topic: currentTopic || "",
      outcome,
      gamesPlayedAtEnd: gamesPlayed,
      voteTally: revealPayload?.vote_tally || {},
      messages: (chatlog || []).map((m) => ({
        name: m?.name || "unknown",
        message: m?.message || ""
      }))
    };
  }

  function appendSessionHistoryOnce(revealPayload){
    if (!sessionId) return;
    const alreadySaved = sessionHistory.some((h)=> h.sessionId === sessionId);
    if (alreadySaved) return;

    const entry = buildSessionHistory(revealPayload);
    sessionHistory = [entry, ...sessionHistory].slice(0, HISTORY_LIMIT);
    saveSessionHistory();
  }

  function recordStatsFromReveal(data){
    if (alreadyRevealed) return;
    const outcome = getPlayerOutcome(data);

    if (outcome === "win"){
      humanWins += 1;
    } else if (outcome === "lose"){
      humanLosses += 1;
    }
    gamesPlayed += 1;
    alreadyRevealed = true;
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
      gameDurationSeconds,
      players,
      chatlog,
      gamePhase,
      countdownSeconds,
      suspectId,
      revealData,
      voteTally,
      voteCounts,
      humanWins,
      humanLosses,
      gamesPlayed,
      hasVoted,
      currentTopic
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
      gameDurationSeconds = Number(data.gameDurationSeconds || 60);
      voteTally = data.voteTally || {};
      voteCounts = data.voteCounts || {};
      humanWins = data.humanWins || 0;
      humanLosses = data.humanLosses || 0;
      gamesPlayed = data.gamesPlayed || 0;
      hasVoted = data.hasVoted || false;
      currentTopic = data.currentTopic || "";
    } catch (err) {
      localStorage.removeItem(APP_STATE_KEY);
    }
  }

  function clearUiState(){
    localStorage.removeItem(APP_STATE_KEY);
  }

  function loadSessionHistory(){
    const raw = localStorage.getItem(CHAT_HISTORY_KEY);
    if (!raw) {
      sessionHistory = [];
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      sessionHistory = Array.isArray(parsed) ? parsed : [];
    } catch {
      sessionHistory = [];
      localStorage.removeItem(CHAT_HISTORY_KEY);
    }
    }

  function saveSessionHistory(){
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(sessionHistory));
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
    voteTally = {};
    voteCounts = {};
    hasVoted = false;
    alreadyRevealed = false;
    currentTopic = "";
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
        <li>If this is the first time in a while you might need to wait up to a minute for the backend to wake up from sleep (render.com free tier thing)</li>
      </ul>
      `
    })
  }

  function exportChat(){
    if (chatlog. length === 0){
      status = "no messages haha";
      return;
    }

    let textContent = "";
    textContent += `game: ${currentTopic}\n`;
    textContent += `players: ${players.map(p=> p.name).join(", ")}\n`;
    textContent += `---\n\n`;
    chatlog.forEach(msg =>{
      textContent += `${msg.name}: ${msg.message}\n`;
    })

    downloadFile(textContent, `chat_${sessionId}.txt`, 'text/plain');
  }

  function downloadFile(content, filename, mimeType){
    const blob = new Blob([content], {type:mimeType});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    status = `chat exported as ${filename}`;
  }

  showInstructions();

  let sessionId ="";

  let messageText = "";
  let players = [];

  let revealData=null;
  let chatlog = [];

  let humanName = "";
  let gameDurationSeconds = 60;
  let botTickTimer = null;

  let gamePhase = "chat"
  let countdownSeconds = 0;
  let phaseTimer = null;

  let currentPlayerId = "";
  let suspectId = "";

  let previousPhase = "chat";
  let alreadyRevealed = false;

  let voteTally = {};
  let voteCounts = {};
  let humanWins = 0;
  let humanLosses = 0;
  let gamesPlayed = 0;
  let isBackendStarting = false;
  let wakeMessage = "";
  let wakeStarted =0;

  let hasVoted = false;

  let currentTopic = "";

  restoreUiState();
  loadSessionHistory();
  if (sessionId){
    if (botTickTimer) clearInterval(botTickTimer);
    botTickTimer = setInterval(botTick, 3000);

    if (phaseTimer) clearInterval(phaseTimer);
    phaseTimer = setInterval(loadGamesState, 1000);
    loadGamesState();
  }

  import Wakethingy from "./lib/components/Wakethingy.svelte";
  import Sessionsetup from "./lib/components/Sessionsetup.svelte";
  import Statspanel from "./lib/components/Statspanel.svelte";
</script> 

<main class="app-shell min-h-screen px-4 py-6 sm:px-6 flex flex-col items-center">
  <header>
    <h1>Humane</h1>
  </header>
  <button on:click={showInstructions} class="case-button mb-4">How to play</button>

  <Wakethingy {isBackendStarting} {wakeMessage}/>

  {#if !sessionId}
  <Sessionsetup bind:humanName bind:gameDurationSeconds {status} {createSession} {sessionHistory} {clearSessionHistory}/>
  {/if}

  {#if sessionId && gamePhase !== "reveal"}
    <span class="case-label">Game Phase:{gamePhase}</span>
    {#if gamePhase === "chat"}

    {#if currentTopic}
    <span class="case-label">topic: {currentTopic}</span>
    {/if}

    <div class="chat-container">
      <div class="chat-panel case-panel">
        <div class="chat-log">
          {#each chatlog as msg, i(`${msg.timestamp}-${msg.name}-${i}`)}
            <div class="chat-message">
              <strong>{msg.name}:</strong> {msg.message}
            </div>
            {/each}
        </div>
        <div class="chat-input-row">
          <input type="text" placeholder="type your message" bind:value={messageText} on:keydown={handleMessageKeydown} class="case-input"/>
          <button on:click={sendMessage} class="case-button case-button-primary">
            send
          </button>
        </div>
        <button on:click={exportChat} class="case-button" style="margin-top:8px;">
          export chat
        </button>
      </div>
      
      <Statspanel {gamesPlayed} {humanWins} {humanLosses} {countdownSeconds} {resetGame}/>

    </div>
  {/if}
  {#if gamePhase === "voting"}
  <div class="max-w-md">
    <span class="case-label">Select a suspect</span>
    <div class="case-panel">
      <div class="vote-grid">
        {#each players as p (p.player_id)}
          <button on:click={()=> (suspectId = p.player_id)} class="vote-button {suspectId === p.player_id ? 'selected' : ''}" disabled={hasVoted}>
          {p.name}</button>
          {/each}
      </div>
      <button on:click={submitVote} class="case-button case-button-primary" style="width: 100%" disabled={hasVoted || !suspectId}>Vote</button>
      
    </div>
  </div>
  {/if}{/if}

  {#if gamePhase === "reveal"}
    <div class="reveal-section">
      <div class="case-label">Results</div>
      <div class="case-panel">
        <div class="reveal-title">{getPlayerOutcome(revealData) === "win" ? "You win": "You Lose"}</div>
        {#if revealData?.vote_tally}
        <div class="vote-tally">{tallyText()}</div>
        {/if}
        {#if currentTopic}
        <span class="case-label">Topic: {currentTopic}</span>
        {/if}

        <button on:click={resetGame} class="case-button case-button-primary" style="width:100%;">new game</button>
      </div>
    </div>
    {/if}
</main>