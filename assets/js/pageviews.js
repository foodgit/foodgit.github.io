document.addEventListener('DOMContentLoaded', async () => {
  const pageKey = encodeURIComponent(location.pathname);
  const namespace = 'gitfood2025';
  const counter = document.getElementById('counter');

  try {
    const response = await fetch(`https://api.countapi.dev/hit/${namespace}/${pageKey}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    counter.textContent = data.value;
  } catch (error) {
    console.error('Pageview counter error:', error);
    counter.textContent = 'error';
  }
});