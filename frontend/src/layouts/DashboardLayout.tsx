import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileSearch, 
  Layers, 
  Mic, 
  BarChart2
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Screening', path: '/screening', icon: FileSearch },
    { name: 'Batch Screening', path: '/multi-screening', icon: Layers },
    { name: 'Interview Copilot', path: '/copilot', icon: Mic },
    { name: 'Analytics', path: '/analytics', icon: BarChart2 }
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      {/* Sidebar Panel */}
      <aside className="w-64 flex-shrink-0 border-r border-slate-200 bg-slate-900 text-slate-300 flex flex-col justify-between">
        <div>
          {/* Logo brand header */}
          <div className="flex h-16 items-center px-6 border-b border-slate-800 bg-slate-950">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-white font-extrabold text-sm shadow-md">
              HG
            </div>
            <span className="ml-3 text-lg font-bold text-white tracking-wide">
              HireGen AI
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="mt-6 px-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 group ${
                    isActive
                      ? 'bg-primary text-white shadow-md'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className={`mr-3 h-5 w-5 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'}`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header bar */}
        <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-8 shadow-sm">
          <h1 className="text-lg font-bold text-slate-800">
            {navItems.find((item) => item.path === location.pathname)?.name || 'Recruiter Portal'}
          </h1>
        </header>

        {/* Dynamic Route Children Outlet */}
        <main className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
export default DashboardLayout;
