import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import DashboardLayout from './layouts/DashboardLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Screening from './pages/Screening';
import MultiScreening from './pages/MultiScreening';
import Copilot from './pages/Copilot';
import Analytics from './pages/Analytics';
import CandidateProfile from './pages/CandidateProfile';

export const App: React.FC = () => {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        {/* Secure SaaS panel routes */}
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="screening" element={<Screening />} />
          <Route path="multi-screening" element={<MultiScreening />} />
          <Route path="copilot" element={<Copilot />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="candidate/:id" element={<CandidateProfile />} />
          {/* Fallback routes */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
export default App;
