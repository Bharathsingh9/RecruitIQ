import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Candidate, KPIStats } from '../types/candidate';
import { 
  Users, 
  CheckCircle, 
  HelpCircle, 
  Award, 
  Download, 
  Trash2, 
  Search,
  ChevronRight,
  TrendingUp,
  FileDown
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [kpis, setKpis] = useState<KPIStats>({
    total: 0,
    shortlisted: 0,
    needs_review: 0,
    rejected: 0,
    average_score: 0
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [predictionFilter, setPredictionFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isExportingExcel, setIsExportingExcel] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Fetch leaderboard
      const leaderboardRes = await api.get<Candidate[]>('/batch/leaderboard', {
        params: {
          search: searchQuery,
          prediction: predictionFilter
        }
      });
      setCandidates(leaderboardRes.data);

      // Fetch analytics KPIs
      const analyticsRes = await api.get('/analytics/kpis');
      if (analyticsRes.data && analyticsRes.data.kpis) {
        setKpis(analyticsRes.data.kpis);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [searchQuery, predictionFilter]);

  const handleDelete = async (candId: number) => {
    if (window.confirm('Are you sure you want to delete this candidate record?')) {
      try {
        await api.delete(`/batch/candidate/${candId}`);
        fetchData();
      } catch (err) {
        console.error('Failed to delete candidate:', err);
      }
    }
  };

  const handleDownloadPDF = async (candId: number, candName: string) => {
    try {
      const response = await api.get(`/reports/pdf/candidate/${candId}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Evaluation_Report_${candName.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download PDF:', err);
    }
  };

  const handleExportExcel = async () => {
    setIsExportingExcel(true);
    try {
      const response = await api.get('/reports/excel/campaign', {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Campaign_Recruiter_Report.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to export campaign Excel spreadsheet:', err);
    } finally {
      setIsExportingExcel(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Welcome Title */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Hiring Overview</h2>
          <p className="text-sm text-slate-500 mt-1">Monitor your active hiring pipeline and candidate rankings.</p>
        </div>
        <button
          onClick={handleExportExcel}
          disabled={isExportingExcel || candidates.length === 0}
          className="flex items-center justify-center px-4 py-2 border border-primary text-primary hover:bg-primary hover:text-white rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:hover:bg-transparent disabled:hover:text-primary shadow-sm"
        >
          <FileDown className="mr-2 h-4 w-4" />
          {isExportingExcel ? 'Exporting Report...' : 'Export Hiring Report'}
        </button>
      </div>

      {/* KPI Stats Panel */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* KPI: Total Screened */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Candidates</p>
            <h3 className="text-2xl font-extrabold text-slate-800 mt-2">{kpis.total}</h3>
          </div>
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Users className="h-6 w-6" />
          </div>
        </div>

        {/* KPI: Shortlisted */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Shortlisted Candidates</p>
            <h3 className="text-2xl font-extrabold text-emerald-600 mt-2">{kpis.shortlisted}</h3>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>

        {/* KPI: Needs Review */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Needs Review</p>
            <h3 className="text-2xl font-extrabold text-amber-500 mt-2">{kpis.needs_review}</h3>
          </div>
          <div className="p-3 bg-amber-50 text-amber-500 rounded-lg">
            <HelpCircle className="h-6 w-6" />
          </div>
        </div>

        {/* KPI: Average Score */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Match Score</p>
            <h3 className="text-2xl font-extrabold text-indigo-600 mt-2">{kpis.average_score}%</h3>
          </div>
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Award className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Leaderboard Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table Header Controls */}
        <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <h3 className="text-lg font-bold text-slate-800">Candidate Rankings</h3>
          
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
            {/* Search inputs */}
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-slate-400" />
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search candidates/skills..."
                className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-64 transition"
              />
            </div>

            {/* Prediction category filter select dropdown */}
            <select
              value={predictionFilter}
              onChange={(e) => setPredictionFilter(e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-lg text-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
            >
              <option value="">All Statuses</option>
              <option value="Shortlist">Shortlisted</option>
              <option value="Needs Review">Needs Review</option>
              <option value="Reject">Rejected</option>
            </select>
          </div>
        </div>

        {/* Table Grid */}
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
            </div>
          ) : candidates.length === 0 ? (
            <div className="text-center py-16 flex flex-col items-center justify-center">
              <div className="bg-slate-100 p-4 rounded-full mb-4">
                <Users className="h-8 w-8 text-slate-400" />
              </div>
              <h3 className="text-base font-bold text-slate-700 mb-1">No candidates screened yet.</h3>
              <p className="text-slate-400 text-sm mb-6">Upload and analyze a resume to populate the candidate rankings.</p>
              <Link
                to="/screening"
                className="bg-primary hover:bg-primary-hover text-white px-6 py-2 rounded-lg font-semibold text-sm transition shadow-sm"
              >
                Upload Resume
              </Link>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-4 px-6 text-center w-16">Rank</th>
                  <th className="py-4 px-6">Candidate Name</th>
                  <th className="py-4 px-6 text-center">JD Match %</th>
                  <th className="py-4 px-6 text-center">Resume Score</th>
                  <th className="py-4 px-6 text-center">Experience</th>
                  <th className="py-4 px-6 text-center">Recommendation</th>
                  <th className="py-4 px-6 text-center">Rank Score</th>
                  <th className="py-4 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {candidates.map((cand) => (
                  <tr key={cand.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-4 px-6 text-center font-bold text-slate-500">
                      {cand.rank}
                    </td>
                    <td className="py-4 px-6">
                      <div>
                        <p className="font-bold text-slate-800">{cand.name}</p>
                        <p className="text-xs text-slate-400 truncate w-48">{cand.email || 'No email'}</p>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-center font-semibold text-indigo-600">
                      {cand.resume_score}%
                    </td>
                    <td className="py-4 px-6 text-center">
                      <span className="font-semibold text-slate-800">{cand.overall_resume_score}</span>
                      <span className="text-xs text-slate-400 ml-1">({cand.grade})</span>
                    </td>
                    <td className="py-4 px-6 text-center">
                      {cand.experience_years} Years
                    </td>
                    <td className="py-4 px-6 text-center">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        cand.prediction === 'Shortlist'
                          ? 'bg-emerald-50 text-emerald-700'
                          : cand.prediction === 'Needs Review'
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-red-50 text-red-700'
                      }`}>
                        {cand.prediction}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <TrendingUp className="h-3 w-3 text-primary" />
                        <span className="font-extrabold text-primary">{cand.rank_score}%</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleDownloadPDF(cand.id, cand.name)}
                          title="Download PDF Dossier"
                          className="p-1.5 border border-slate-200 hover:border-slate-300 text-slate-500 hover:text-slate-700 rounded-lg transition"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(cand.id)}
                          title="Delete Application"
                          className="p-1.5 border border-red-200 hover:border-red-300 text-red-500 hover:text-red-700 rounded-lg transition"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        <Link
                          to={`/candidate/${cand.id}`}
                          title="View Analysis Details"
                          className="p-1.5 bg-primary text-white hover:bg-primary-hover rounded-lg transition flex items-center justify-center"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
