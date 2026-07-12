import { createRoot } from 'react-dom/client';
import { App } from './App';
import './styles.css';

createRoot(document.getElementById('root')!).render(<App />);

// PWA: 本番ビルドでのみ Service Worker を登録(開発時は Vite が UI を配信するため)
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}
