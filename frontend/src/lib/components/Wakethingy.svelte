  <script>
    export let isBackendStarting = false;
    export let wakeMessage = "";
  </script>
  
  {#if isBackendStarting}
    <div class="wake-background">
      <div class="wake-card">
        <div class="wake-spin-thing">
        </div>
        <h3>Connecting to backend</h3> 
          <p>{wakeMessage}</p>
          <p class="wake-sub">first request can take a bit of time.</p>
      </div>
    </div>
    {/if}