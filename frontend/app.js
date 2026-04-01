import { bootstrap } from './core/bootstrap.js';

bootstrap().catch((error) => {
  console.error('UI bootstrap failed', error);
  const feedback = document.getElementById('command-feedback');
  if (feedback) feedback.textContent = 'Bootstrap failed';
  const banner = document.getElementById('no-data-banner');
  if (banner) {
    banner.textContent = 'UI BOOTSTRAP FAILED';
    banner.style.display = 'block';
  }
});
