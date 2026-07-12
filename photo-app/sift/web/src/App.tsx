import { useEffect, useState } from 'react';
import { Home } from './screens/Home';
import { Swipe } from './screens/Swipe';
import { Duplicates } from './screens/Duplicates';
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
  if (route.startsWith('/swipe/')) return <Swipe category={route.slice('/swipe/'.length)} />;
  if (route === '/duplicates') return <Duplicates />;
  if (route === '/trash') return <Trash />;
  return <Home />;
}
