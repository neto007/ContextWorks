import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Suppress Monaco Editor benign cancellation errors
window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
  if (event.reason?.type === 'cancelation' && event.reason?.msg === 'operation is manually canceled') {
    event.preventDefault();
  }
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
