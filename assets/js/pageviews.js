document.addEventListener('DOMContentLoaded', function () {
  const path = window.location.pathname.replace(/[^\w]/g, '_');
  const endpoint = `https://api.myjson.online/v1/records/${path}`;

  fetch(endpoint)
    .then(res => res.json())
    .then(data => {
      const count = (data?.data?.views || 0) + 1;
      document.getElementById('counter').textContent = count;

      return fetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ views: count }),
      });
    })
    .catch(err => {
      console.error('Counter error:', err);
      document.getElementById('counter').textContent = 'error';
    });
});
