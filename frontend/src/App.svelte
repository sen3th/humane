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

  let sessionId ="";
</script>

<main>
  <h1>Humane :)</h1>
  <button on:click={checkBackend}>Check Backend</button>
  <p>Backend says: {status}</p>
  <p>Session ID: {sessionId}</p>
  <button on:click={createSession}>make Session</button>
</main>