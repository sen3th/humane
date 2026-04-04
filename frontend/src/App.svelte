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
    
    clearUiState();
    try {
      const res = await fetch("https://humane-1-dznm.onrender.com/sessions",{
        method : "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          human_name: humanName,
          bot_count: 3,
          chat_duration_seconds: gameDurationSeconds
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
      messageText = ""
      status = `${data.name} says: ${data.message}`;
      saveUiState();
      botTick();
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
      if (data.revealOutcome === "win") humanWins += 1;
      else if(data.playerOutcome === "lose") humanLosses += 1;
      gamesPlayed +=1;
      saveUiState();
      await showOutcomeAlert(data.playerOutcome);
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
        const parsedSeconds = Number(data.chat_seconds_left ?? data.seconds_left ?? 0);
        countdownSeconds = Number.isFinite(parsedSeconds) ? Math.max(0, Math.floor(parsedSeconds)) : 0;
        voteTally = data.vote_tally || {};
        voteCounts = data.vote_counts || {};
        saveUiState();

        if (gamePhase === "reveal" && !revealData && data.reveal_data) {
          revealData = data.reveal_data;
          await showOutcomeAlert(revealData.playerOutcome);
          status = "Reveal ready";
          saveUiState();
        }
      }
    }catch (err) {
      console.error("can't load game state", err);
    }
  }

  function tallyText(){
    const lines = Object.entries(voteCounts).map(
      ([id, count]) => `${getPlayerNameById(id)}:${count}`
  ); return lines.length?`Vote tally:\n${lines.join("\n")}\n\n`:"";
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
      gamesPlayed
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
    voteTally = {};
    voteCounts = {};
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

  restoreUiState();
  if (sessionId){
    if (botTickTimer) clearInterval(botTickTimer);
    botTickTimer = setInterval(botTick, 3000);

    if (phaseTimer) clearInterval(phaseTimer);
    phaseTimer = setInterval(loadGamesState, 1000);
    loadGamesState();
  }
</script>

<main class="app-shell min-h-screen px-4 py-6 sm:px-6">
  <header>
    <h1>Humane</h1>
  </header>
</main>