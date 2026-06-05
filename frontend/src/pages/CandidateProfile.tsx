import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { Candidate } from '../types/candidate';
import { 
  FileText, 
  Check, 
  X, 
  HelpCircle, 
  Download,
  AlertCircle,
  ChevronLeft,
  Lightbulb,
  Award,
  Briefcase
} from 'lucide-react';

interface CandidateProfileResult extends Candidate {
  confidence: number;
  overall_resume_score: number;
  grade: string;
  xai_factors: string[];
  shap_values: Record<string, number>;
  questions: {
    technical_questions: string[];
    behavioral_questions: string[];
  };
}

export const CandidateProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<CandidateProfileResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const fetchCandidateDetails = async () => {
      if (!id) return;
      setIsLoading(true);
      setErrorMsg('');
      try {
        const response = await api.get<CandidateProfileResult>(`/batch/candidate/${id}`);
        setResult(response.data);
      } catch (err: any) {
        console.error('Failed to load candidate details:', err);
        setErrorMsg('Failed to load candidate profile details.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCandidateDetails();
  }, [id]);

  const handleDownloadPDF = async () => {
    if (!result) return;
    try {
      const response = await api.get(`/reports/pdf/candidate/${result.id}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Evaluation_Report_${result.name.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download PDF:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (errorMsg || !result) {
    return (
      <div className="p-8">
        <div className="rounded-lg bg-red-50 p-4 border border-red-100 text-sm text-red-600 flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{errorMsg || 'Candidate not found.'}</span>
        </div>
        <Link to="/dashboard" className="mt-4 inline-flex items-center text-primary font-semibold text-sm hover:underline">
          <ChevronLeft className="mr-1 h-4 w-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 animate-fade-in">
      <Link to="/dashboard" className="inline-flex items-center text-slate-500 font-semibold text-sm hover:text-primary transition mb-2">
        <ChevronLeft className="mr-1 h-4 w-4" /> Back to Dashboard
      </Link>

      {/* Headline Results Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-6 md:space-y-0">
          <div className="flex items-center space-x-5">
            <div className="h-16 w-16 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center font-extrabold text-2xl text-slate-700 shadow-inner">
              {result.name.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-800 tracking-tight">{result.name}</h2>
              <div className="flex flex-wrap items-center text-sm font-medium text-slate-500 mt-2 gap-x-4 gap-y-2">
                <span className="flex items-center"><Briefcase className="h-4 w-4 mr-1" /> {result.experience_years} Yrs Exp</span>
                <span>•</span>
                <span>{result.email || 'No Email'}</span>
                <span>•</span>
                <span>{result.phone || 'No Phone'}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={handleDownloadPDF}
              className="flex items-center px-4 py-2 border border-slate-200 hover:border-slate-300 text-slate-600 hover:text-slate-800 rounded-lg text-sm font-bold transition shadow-sm"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Report
            </button>
            <span className={`px-5 py-2 rounded-lg text-sm font-extrabold shadow-sm ${
              result.prediction === 'Shortlist'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : result.prediction === 'Needs Review'
                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {result.prediction.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Scorecard indicators Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-10 pt-8 border-t border-slate-100 text-center">
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">JD Match Score</p>
            <p className="text-3xl font-extrabold text-indigo-600 mt-2">{result.resume_score}%</p>
          </div>
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Resume Quality</p>
            <p className="text-3xl font-extrabold text-slate-800 mt-2">
              {result.overall_resume_score} <span className="text-sm text-slate-400">({result.grade})</span>
            </p>
          </div>
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Education & Certs</p>
            <p className="text-3xl font-extrabold text-slate-800 mt-2 flex items-center justify-center space-x-2">
              <Award className="h-6 w-6 text-amber-500" />
              <span>{result.certifications}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Skills Profile */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center">
            <FileText className="mr-2 h-5 w-5 text-indigo-500" />
            Skills Analysis
          </h4>
          
          <div className="space-y-6">
            <div>
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-3">
                Matched Requirements ({result.matched_skills.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {result.matched_skills.length === 0 ? (
                  <span className="text-sm font-medium text-slate-400">No matching skills found.</span>
                ) : (
                  result.matched_skills.map((skill) => (
                    <span key={skill} className="px-3 py-1.5 bg-blue-50/80 border border-blue-100 text-blue-700 rounded-lg text-xs font-bold flex items-center shadow-sm">
                      <Check className="mr-1.5 h-3.5 w-3.5" />
                      {skill.toUpperCase()}
                    </span>
                  ))
                )}
              </div>
            </div>

            <div>
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-3">
                Missing Requirements ({result.missing_skills.length})
              </span>
              <div className="flex flex-wrap gap-2">
                {result.missing_skills.length === 0 ? (
                  <span className="text-sm font-medium text-slate-400">Candidate meets all requirements.</span>
                ) : (
                  result.missing_skills.map((skill) => (
                    <span key={skill} className="px-3 py-1.5 bg-red-50/80 border border-red-100 text-red-700 rounded-lg text-xs font-bold flex items-center shadow-sm">
                      <X className="mr-1.5 h-3.5 w-3.5" />
                      {skill.toUpperCase()}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Generative Interview Questions */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center">
            <HelpCircle className="mr-2 h-5 w-5 text-indigo-500" />
            Recommended Interview Questions
          </h4>
          
          <div className="space-y-5 custom-scrollbar max-h-96 overflow-y-auto pr-2">
            {result.questions.technical_questions.length > 0 && (
              <div className="space-y-3">
                <span className="text-[10px] font-extrabold text-indigo-500 uppercase tracking-wider block bg-indigo-50 px-2 py-1 rounded inline-block">
                  Technical
                </span>
                {result.questions.technical_questions.map((q, idx) => (
                  <p key={idx} className="text-sm font-medium text-slate-700 bg-slate-50 p-3.5 rounded-xl border border-slate-100 leading-relaxed">
                    {typeof q === 'string' ? q : (q as any).description || (q as any).question || JSON.stringify(q)}
                  </p>
                ))}
              </div>
            )}

            {result.questions.behavioral_questions.length > 0 && (
              <div className="space-y-3 pt-2">
                <span className="text-[10px] font-extrabold text-emerald-500 uppercase tracking-wider block bg-emerald-50 px-2 py-1 rounded inline-block">
                  Behavioral
                </span>
                {result.questions.behavioral_questions.map((q, idx) => (
                  <p key={idx} className="text-sm font-medium text-slate-700 bg-slate-50 p-3.5 rounded-xl border border-slate-100 leading-relaxed">
                    {typeof q === 'string' ? q : (q as any).description || (q as any).question || JSON.stringify(q)}
                  </p>
                ))}
              </div>
            )}

            {result.questions.technical_questions.length === 0 && result.questions.behavioral_questions.length === 0 && (
              <p className="text-sm font-medium text-slate-400 text-center py-8">No specific screening questions generated for this profile.</p>
            )}
          </div>
        </div>

        {/* AI Match Drivers */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6 md:col-span-2">
          <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center">
            <Lightbulb className="mr-2 h-5 w-5 text-amber-500" />
            AI Match Drivers (Why this score?)
          </h4>

          <div className="space-y-3 columns-1 md:columns-2 gap-8">
            {result.xai_factors.length === 0 ? (
              <p className="text-sm text-slate-400">No detailed factors available.</p>
            ) : (
              result.xai_factors.map((factor, idx) => (
                <div key={idx} className="flex items-start break-inside-avoid mb-4">
                  <div className="flex-shrink-0 h-6 w-6 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500 mr-3 mt-0.5">
                    {idx + 1}
                  </div>
                  <p className="text-sm font-medium text-slate-600 leading-relaxed">
                    {factor}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
export default CandidateProfile;
