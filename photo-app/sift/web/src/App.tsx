import { useEffect, useState } from 'react';
import { api, ApiError } from './api';
import { PinGate } from './components/PinGate';
import { Home } from './screens/Home';
import { Swipe } from './screens/Swipe';
import { Groups } from './screens/Groups';
import { Settings } from './screens/Settings';
import { Stats } from './screens/Stats';
import { Trash } from './screens/Trash';

function useHashRoute(): string {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return hash.replace(/^#/, '') || '/';
}

export function App() {
  const route = useHashRoute();
  // PIN が必要か初回に確認(SIFT_PIN 未設定なら即 ok)
  const [auth, setAuth] = useState<'loading' | 'ok' | 'pin'>('loading');
  useEffect(() => {
    api
      .health()
      .then(() => setAuth('ok'))
      .catch((e) => setAuth(e instanceof ApiError && e.status === 401 ? 'pin' : 'ok'));
  }, []);

  if (auth === 'loading') return <p className="pt-32 text-center text-neutral-500">読み込み中…</p>;
  if (auth === 'pin') return <PinGate onOk={() => setAuth('ok')} />;

  if (route.startsWith('/swipe/')) return <Swipe category={route.slice('/swipe/'.length)} />;
  if (route === '/groups' || route === '/duplicates') return <Groups />;
  if (route === '/stats') return <Stats />;
  if (route === '/settings') return <Settings />;
  if (route === '/trash') return <Trash />;
  return <Home />;
}
