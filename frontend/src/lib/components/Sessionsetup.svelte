<script>
    export let humanName = "";
    export let gameDurationSeconds = 60;
    export let status = "";
    export let createSession = ()=>{};
    export let sessionHistory = [];
    export let clearSessionHistory = ()=>{};
</script>

<div class="max-w-md">
    <span class="case-label">Session setup</span>
    <div class="case-panel setup-form">
      <input type="text" placeholder="Enter a name" bind:value={humanName} class="case-input"/>
      <input type="number" placeholder="duration in seconds" bind:value={gameDurationSeconds} class="case-input"/>
      <button on:click={createSession} class="case-button case-button-primary">
        Create Session
      </button>
    </div>
    {#if status}
    <p class="text-xs mt-2">{status}</p>
    {/if}

    {#if sessionHistory.length}
    <div class="case-panel mt-4">
      <div class="flex items-center justify-between mb-2">
        <span class="case-label">session history</span>
        <button class="case-button" on:click={clearSessionHistory}>Clear</button>
      </div>

      <div class="space-y-3">
        {#each sessionHistory as h (h.id)}
        <details class="history-item">
          <summary class="history-summary">
            {new Date(h.createdAt).toLocaleString()}, you {h.outcome || "unknown"} . {h.topic || "no top"}
          </summary>
          <div class="history-meta">sessionid: {h.sessionId}</div>
          <div class="history-meta">Messages: {h.messages?.length || 0}</div>

          {#if h.messages?.length}
          <div class="history-chat">
            {#each h.messages as m, i(`${h.id}-${i}`)}
            <div><strong>{m.name}:</strong>{m.message}</div>
            {/each}
          </div>
          {/if}
        </details>
        {/each}
      </div>
    </div>
    {/if}
  </div>
