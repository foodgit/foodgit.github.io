// /assets/js/pageviews.js

(function () {
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
})();
// This script fetches the current view count for the page, increments it, and updates the display.
// It uses a JSON API to store and retrieve the view count, ensuring that each page view is counted accurately.
// The view count is displayed in the element with ID 'counter'.