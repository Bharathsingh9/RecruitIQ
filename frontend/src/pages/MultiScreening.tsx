import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Candidate } from '../types/candidate';
import { 
  Upload, 
  Layers, 
  FileText, 
  CheckCircle2, 
  AlertTriangle,
  RefreshCw,
  Search,
  Download,
  Trash2,
  ChevronRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface BatchResult {
  id: number;
  name: string;
  prediction: string;
  score: number;
}

interface BatchStatusResponse {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  processed: number;
  total: number;
  errors: { filename: string; error: string }[];
  results: BatchResult[];
}

export const MultiScreening: React.FC = () => {
  // Input states
  const [files, setFiles] = useState<FileList | null>(null);
  const [jdText, setJdText] = useState('');
  const [experienceYears, setExperienceYears] = useState(3.0);
  const [educationScore, setEducationScore] = useState(80.0);
  const [certifications, setCertifications] = useState(1);
  const [projects, setProjects] = useState('');

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Async batch task states
  const [taskId, setTaskId] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<BatchStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Leaderboard states
  const [leaderboard, setLeaderboard] = useState<Candidate[]>([]);
  const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(e.target.files);
    }
  };

  const handleBatchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) {
      setErrorMsg('Please select one or more candidate resume PDFs.');
      return;
    }
    if (!jdText.trim()) {
      setErrorMsg('Please specify target job description requirements.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    setTaskId(null);
    setBatchStatus(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('jd_text', jdText);
    formData.append('experience_years', experienceYears.toString());
    formData.append('education_score', educationScore.toString());
    formData.append('certifications', certifications.toString());
    formData.append('projects', projects);

    try {
      const response = await api.post('/batch/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setTaskId(response.data.task_id);
      setIsPolling(true);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Batch campaign initialization failed.');
      setIsSubmitting(false);
    }
  };

  // Poll status endpoint while task is active
  useEffect(() => {
    if (!taskId || !isPolling) return;

    let intervalId: ReturnType<typeof setInterval>;

    const checkStatus = async () => {
      try {
        const response = await api.get<BatchStatusResponse>(`/batch/status/${taskId}`);
        setBatchStatus(response.data);
        
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setIsPolling(false);
          setIsSubmitting(false);
          fetchLeaderboard(); // Refresh leaderboard to include newly processed records
        }
      } catch (err) {
        console.error('Failed to query batch task status:', err);
        setIsPolling(false);
        setIsSubmitting(false);
      }
    };

    // Run immediately and then poll every 2 seconds
    checkStatus();
    intervalId = setInterval(checkStatus, 2000);

    return () => clearInterval(intervalId);
  }, [taskId, isPolling]);

  const fetchLeaderboard = async () => {
    setIsLoadingLeaderboard(true);
    try {
      const response = await api.get<Candidate[]>('/batch/leaderboard', {
        params: { search: searchQuery }
      });
      setLeaderboard(response.data);
    } catch (err) {
      console.error('Error fetching campaign rankings:', err);
    } finally {
      setIsLoadingLeaderboard(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, [searchQuery]);

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

  const handleDelete = async (candId: number) => {
    if (window.confirm('Delete this candidate evaluation profile?')) {
      try {
        await api.delete(`/batch/candidate/${candId}`);
        fetchLeaderboard();
      } catch (err) {
        console.error('Delete candidate record failed:', err);
      }
    }
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Form side (Span 1/3) */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-base font-bold text-slate-800 mb-6 flex items-center">
              Bulk Resume Upload
            </h3>

            {errorMsg && (
              <div className="rounded-lg bg-red-50 p-4 border border-red-100 text-xs text-red-600 mb-6">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleBatchSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Select Candidate Resumes (PDF list)
                </label>
                <div className="border-2 border-dashed border-slate-200 hover:border-primary rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50/50 hover:bg-slate-50 transition relative">
                  <input
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFilesChange}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <Upload className="h-8 w-8 text-slate-400 mb-2" />
                  <span className="text-xs font-semibold text-slate-600 text-center">
                    {files && files.length > 0 ? `${files.length} PDF files selected` : 'Select Multiple PDFs'}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Job Description requirements
                </label>
                <textarea
                  required
                  rows={4}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="e.g. Scikit-learn, SQL, Docker, FastAPI..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-800 text-xs focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition custom-scrollbar"
                />
              </div>

              {/* Advanced configs hidden for recruiter simplicity */}

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-primary hover:bg-primary-hover text-white py-2 rounded-lg font-semibold text-xs transition shadow-sm disabled:opacity-50 flex items-center justify-center"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="animate-spin mr-2 h-4 w-4" />
                    Analyzing...
                  </>
                ) : (
                  'Analyze Candidates'
                )}
              </button>
            </form>
          </div>

          {/* Active Campaign Status Polling Card */}
          {batchStatus && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-800">Bulk Screening Progress</h4>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  batchStatus.status === 'completed'
                    ? 'bg-emerald-50 text-emerald-700'
                    : batchStatus.status === 'failed'
                    ? 'bg-red-50 text-red-700'
                    : 'bg-blue-50 text-blue-700 animate-pulse'
                }`}>
                  {batchStatus.status}
                </span>
              </div>

              {/* Progress bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Processed Resumes</span>
                  <span className="font-bold">{batchStatus.processed} of {batchStatus.total}</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${(batchStatus.processed / batchStatus.total) * 100}%` }}
                    className="h-full bg-primary transition-all duration-300"
                  ></div>
                </div>
              </div>

              {/* Error list */}
              {batchStatus.errors.length > 0 && (
                <div className="pt-3 border-t border-slate-100 space-y-2">
                  <span className="text-[10px] font-bold text-red-500 uppercase tracking-wider block">
                    Errors ({batchStatus.errors.length})
                  </span>
                  <div className="max-h-24 overflow-y-auto space-y-1.5 custom-scrollbar pr-1">
                    {batchStatus.errors.map((err, idx) => (
                      <div key={idx} className="flex items-start space-x-1.5 text-xs text-red-600 bg-red-50/50 p-1.5 rounded border border-red-50">
                        <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
                        <span className="break-all"><b>{err.filename}:</b> {err.error}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Campaign Ranking List Leaderboard (Span 2/3) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div>
              <h3 className="font-bold text-slate-800 text-base">Candidate Rankings</h3>
              <p className="text-xs text-slate-400 mt-1">Review candidate rank ordered by match index.</p>
            </div>
            
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-3.5 w-3.5 text-slate-400" />
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Quick search..."
                className="pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg text-slate-800 text-xs focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-48 transition"
              />
            </div>
          </div>

          {/* List Table */}
          <div className="overflow-x-auto flex-1">
            {isLoadingLeaderboard ? (
              <div className="flex justify-center items-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
              </div>
            ) : leaderboard.length === 0 ? (
              <div className="text-center py-24 flex flex-col items-center justify-center">
                <div className="bg-slate-100 p-4 rounded-full mb-4">
                  <Layers className="h-8 w-8 text-slate-400" />
                </div>
                <h3 className="text-base font-bold text-slate-700 mb-1">No candidates screened yet.</h3>
                <p className="text-slate-400 text-sm">Upload and analyze a resume to populate the candidate rankings.</p>
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-6 text-center w-12">Rank</th>
                    <th className="py-3 px-6">Name</th>
                    <th className="py-3 px-6 text-center">Match %</th>
                    <th className="py-3 px-6 text-center">Score</th>
                    <th className="py-3 px-6 text-center">Status</th>
                    <th className="py-3 px-6 text-center">Rank Score</th>
                    <th className="py-3 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                  {leaderboard.map((cand) => (
                    <tr key={cand.id} className="hover:bg-slate-50/50 transition">
                      <td className="py-3.5 px-6 text-center font-bold text-slate-500">
                        {cand.rank}
                      </td>
                      <td className="py-3.5 px-6">
                        <div>
                          <p className="font-bold text-slate-800">{cand.name}</p>
                          <p className="text-[10px] text-slate-400 truncate w-36">{cand.email || 'No email'}</p>
                        </div>
                      </td>
                      <td className="py-3.5 px-6 text-center font-semibold text-indigo-600">
                        {cand.resume_score}%
                      </td>
                      <td className="py-3.5 px-6 text-center">
                        <span className="font-semibold">{cand.overall_resume_score}</span>
                        <span className="text-[10px] text-slate-400 ml-0.5">({cand.grade})</span>
                      </td>
                      <td className="py-3.5 px-6 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          cand.prediction === 'Shortlist'
                            ? 'bg-emerald-50 text-emerald-700'
                            : cand.prediction === 'Needs Review'
                            ? 'bg-amber-50 text-amber-700'
                            : 'bg-red-50 text-red-700'
                        }`}>
                          {cand.prediction}
                        </span>
                      </td>
                      <td className="py-3.5 px-6 text-center">
                        <span className="font-bold text-primary">{cand.rank_score}%</span>
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={() => handleDownloadPDF(cand.id, cand.name)}
                            title="Download PDF Dossier"
                            className="p-1 border border-slate-200 hover:border-slate-300 text-slate-500 hover:text-slate-700 rounded transition"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(cand.id)}
                            title="Delete"
                            className="p-1 border border-red-200 hover:border-red-300 text-red-500 hover:text-red-700 rounded transition"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                          <Link
                            to={`/candidate/${cand.id}`}
                            className="p-1 bg-primary text-white hover:bg-primary-hover rounded transition flex items-center justify-center"
                          >
                            <ChevronRight className="h-3.5 w-3.5" />
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
    </div>
  );
};
export default MultiScreening;
