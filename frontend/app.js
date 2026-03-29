import { bootstrap } from './core/bootstrap.js';

bootstrap().catch((error) => {
  console.error('UI bootstrap failed', error);
});
