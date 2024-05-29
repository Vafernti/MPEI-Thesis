import React from 'react';
import { createRoot } from 'react-dom/client';
import "bulma/css/bulma.min.css";
import App from './App';
import { UserProvider } from './context/UserContext';  // Corrected the import

// Create a root.
const container = document.getElementById('root');
const root = createRoot(container);

// Initial render
root.render(
  <UserProvider>
    <App />
  </UserProvider>
);
