document.addEventListener('DOMContentLoaded', function () {
  const path = (location.hostname + window.location.pathname).replace(/[^\w]/g, '_');
  const endpoint = `https://api.myjson.online/v1/records/${path}`;

  function updateCounter(count) {
    document.getElementById('counter').textContent = count;
    fetch(endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ views: count }),
    });
  }

  fetch(endpoint)
    .then(res => {
      if (res.status === 404) {
        // Record doesn't exist — create it
        return fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ views: 1 }),
        }).then(() => {
          document.getElementById('counter').textContent = 1;
        });
      } else {
        return res.json().then(data => {
          const current = data?.data?.views || 0;
          const updated = current + 1;
          updateCounter(updated);
        });
      }
    })
    .catch(err => {
      console.error('Counter error:', err);
      document.getElementById('counter').textContent = 'error';
    });
});
