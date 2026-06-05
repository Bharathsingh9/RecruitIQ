import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AnalyticsResponse } from '../types/candidate';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ScatterChart, 
  Scatter
} from 'recharts';
import { 
  TrendingUp, 
  PieChart as PieIcon, 
  BarChart2, 
  Activity, 
  RefreshCw,
  Users
} from 'lucide-react';

export const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<AnalyticsResponse>('/analytics/kpis');
      setData(response.data);
    } catch (err) {
      console.error('Error fetching analytics details:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!data || data.kpis.total === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-16 flex flex-col items-center justify-center text-center">
        <div className="bg-slate-100 p-5 rounded-full mb-4">
          <Activity className="h-10 w-10 text-slate-400" />
        </div>
        <h3 className="text-lg font-bold text-slate-700 mb-2">No hiring analytics available yet</h3>
        <p className="text-slate-500 text-sm max-w-sm">Screen candidates to automatically generate powerful recruitment insights, skills distribution, and score breakdowns.</p>
      </div>
    );
  }

  const PIE_COLORS = ['#10B981', '#F59E0B', '#EF4444']; // Shortlist, Needs Review, Reject HSL colors

  return (
    <div className="space-y-8 animate-fade-in">
      {/* KPIs Summary blocks */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Evaluation Count</p>
            <h3 className="text-xl font-extrabold text-slate-800 mt-1">{data.kpis.total}</h3>
          </div>
          <Users className="h-5 w-5 text-blue-500" />
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Shortlisted Rate</p>
            <h3 className="text-xl font-extrabold text-emerald-600 mt-1">
              {Math.round((data.kpis.shortlisted / data.kpis.total) * 100)}%
            </h3>
          </div>
          <TrendingUp className="h-5 w-5 text-emerald-500" />
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Review Required Rate</p>
            <h3 className="text-xl font-extrabold text-amber-500 mt-1">
              {Math.round((data.kpis.needs_review / data.kpis.total) * 100)}%
            </h3>
          </div>
          <Activity className="h-5 w-5 text-amber-500" />
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Average JD Match</p>
            <h3 className="text-xl font-extrabold text-indigo-600 mt-1">{data.kpis.average_score}%</h3>
          </div>
          <TrendingUp className="h-5 w-5 text-indigo-500" />
        </div>
      </div>

      {/* Grid Charts list */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Chart 1: Prediction Share Pie */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <PieIcon className="mr-2 h-4 w-4 text-emerald-500" />
            Decision Classification Distribution
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.prediction_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {data.prediction_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Experience vs Score Scatter */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <Activity className="mr-2 h-4 w-4 text-indigo-500" />
            Experience (Years) vs. JD Match Score (%)
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="experience" name="Experience" unit=" yrs" />
                <YAxis type="number" dataKey="score" name="Match Score" unit="%" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Candidates" data={data.experience_vs_score} fill="#2563EB" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Top Matched Skills */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <BarChart2 className="mr-2 h-4 w-4 text-blue-500" />
            Top 10 Matched Skills Frequency
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_skills} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="skill" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Top Missing Skills */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <BarChart2 className="mr-2 h-4 w-4 text-red-500" />
            Top 10 Lacking Skills (Talent Gaps)
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_missing_skills} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="skill" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Analytics;
