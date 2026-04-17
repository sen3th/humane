    <script>
    export let gamesPlayed = 0;
    export let humanWins = 0;
    export let humanLosses = 0;
    export let countdownSeconds = 0;
    export let resetGame = ()=>{};
    </script>
    
    <div class="stats-panel">
        <div class="countdown">
          {countdownSeconds}
        </div>
        <div class="stat-item case-panel">
          <div class="stat-value">{gamesPlayed}</div>
          <div class="stat-label">Games played</div>
        </div>
        <div class="stat-item case-panel">
          <div class="stat-value">{humanWins}</div>
          <div class="stat-label">Wins</div>
        </div>
        <div class="stat-item case-panel">
          <div class="stat-value">{humanLosses}</div>
          <div class="stat-label">Losses</div>
        </div>
        <button on:click={resetGame} class="case-button">Reset Stats</button>
      </div>