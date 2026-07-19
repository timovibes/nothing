// minimal router wiring — for now, just the login page, so we can prove the full auth loop works
// before adding the Overview page and protected routing.

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<div className="p-8 font-body">Logged in — dashboard coming next.</div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;