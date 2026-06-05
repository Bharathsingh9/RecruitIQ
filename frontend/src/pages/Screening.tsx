import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Candidate } from '../types/candidate';
import { 
  Upload, 
  FileText, 
  Check, 
  X, 
  HelpCircle, 
  Download,
  AlertCircle
} from 'lucide-react';

interface ScreeningResult extends Candidate {
  confidence: number;
  overall_resume_score: number;
  grade: string;
  xai_factors: string[];
  shap_values: Record<string, number>;
  learning_path: string[];
  questions: {
    technical_questions: string[];
    behavioral_questions: string[];
  };
}

export const Screening: React.FC = () => {
  // Input states
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [experienceYears, setExperienceYears] = useState(3.0);
  const [educationScore, setEducationScore] = useState(80.0);
  const [certifications, setCertifications] = useState(1);
  const [projects, setProjects] = useState('');
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Results state
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Please upload a resume PDF file.');
      return;
    }
    if (!jdText.trim()) {
      setErrorMsg('Please enter a target Job Description.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('jd_text', jdText);
    formData.append('experience_years', experienceYears.toString());
    formData.append('education_score', educationScore.toString());
    formData.append('certifications', certifications.toString());
    formData.append('projects', projects);

    try {
      const response = await api.post('/screening/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      // The API return structure matches ScreeningResult
      const data = response.data;
      setResult({
        id: data.candidate_id,
        name: data.name,
        email: data.email,
        phone: data.phone,
        resume_score: data.match_score,
        overall_resume_score: data.resume_score,
        grade: data.grade,
        experience_years: experienceYears,
        education_score: educationScore,
        certifications: certifications,
        prediction: data.prediction,
        confidence: data.confidence,
        matched_skills: data.matched_skills,
        missing_skills: data.missing_skills,
        xai_factors: data.xai_factors,
        shap_values: data.shap_values,
        learning_path: data.learning_path || [],
        questions: data.questions || { technical_questions: [], behavioral_questions: [] },
        created_at: new Date().toISOString()
      });
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Resume analysis failed. Please verify files and settings.');
    } finally {
      setIsSubmitting(false);
    }
  };

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

  return (
    <div className="space-y-8">
      {/* Upload/Configure Frame */}
      {!result && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Resume Screening Parameters</h3>
          
          {errorMsg && (
            <div className="rounded-lg bg-red-50 p-4 border border-red-100 text-sm text-red-600 mb-6 flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleAnalyze} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* File Upload Area */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Upload Resume (PDF only)
                </label>
                <div className="border-2 border-dashed border-slate-200 hover:border-primary rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-50/50 hover:bg-slate-50 transition relative">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <Upload className="h-10 w-10 text-slate-400 mb-3" />
                  <span className="text-sm font-semibold text-slate-600">
                    {file ? file.name : 'Select or Drag PDF Resume'}
                  </span>
                  <span className="text-xs text-slate-400 mt-1">Maximum size 10MB</span>
                </div>
              </div>

              {/* JD Text area */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Target Job Description (JD Requirements)
                </label>
                <textarea
                  required
                  rows={5}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste the target job description requirements here (e.g. Python, SQL, REST APIs, AWS, 3 years experience)..."
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition custom-scrollbar"
                />
              </div>
            </div>

            {/* Advanced configs hidden (values submitted directly via defaults) */}

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-primary hover:bg-primary-hover text-white py-3 rounded-xl font-bold text-sm transition shadow-md hover:shadow-lg disabled:opacity-50"
            >
              {isSubmitting ? 'Analyzing Candidate...' : 'Analyze Candidate'}
            </button>
          </form>
        </div>
      )}

      {/* Details loading state */}
      {isLoadingDetails && (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
        </div>
      )}

      {/* Assessment Results Section */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          {/* Headline Results Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
              <div className="flex items-center space-x-4">
                <div className="h-14 w-14 rounded-full bg-slate-100 flex items-center justify-center font-bold text-xl text-slate-600">
                  {result.name.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-800">{result.name}</h3>
                  <div className="flex flex-wrap text-xs text-slate-400 mt-1 gap-x-4 gap-y-1">
                    <span>{result.email || 'No Email Address'}</span>
                    <span>•</span>
                    <span>{result.phone || 'No Phone Number'}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={handleDownloadPDF}
                  className="flex items-center px-4 py-2 border border-slate-200 hover:border-slate-300 text-slate-600 hover:text-slate-800 rounded-lg text-sm font-semibold transition"
                >
                  <Download className="mr-2 h-4 w-4" />
                  PDF Dossier
                </button>
                <span className={`px-4 py-2 rounded-lg text-sm font-extrabold shadow-sm ${
                  result.prediction === 'Shortlist'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : result.prediction === 'Needs Review'
                    ? 'bg-amber-50 text-amber-700 border border-amber-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {result.prediction.toUpperCase()} ({Math.round((result.confidence || 0.8) * 100)}%)
                </span>
              </div>
            </div>

            {/* Scorecard indicators Row */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slate-100 text-center">
              <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">JD Match Score</p>
                <p className="text-2xl font-extrabold text-slate-800 mt-1">{result.resume_score}%</p>
              </div>
              <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resume Score</p>
                <p className="text-2xl font-extrabold text-slate-800 mt-1">
                  {result.overall_resume_score} <span className="text-xs text-slate-400">({result.grade})</span>
                </p>
              </div>
              <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Experience Level</p>
                <p className="text-2xl font-extrabold text-slate-800 mt-1">{result.experience_years} Years</p>
              </div>
              <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Certifications</p>
                <p className="text-2xl font-extrabold text-slate-800 mt-1">{result.certifications}</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Skills Profile */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
              <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center">
                <FileText className="mr-2 h-5 w-5 text-indigo-500" />
                Skills Taxonomy Profile
              </h4>
              
              <div className="space-y-4">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Matched Required Skills ({result.matched_skills.length})
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {result.matched_skills.length === 0 ? (
                      <span className="text-sm text-slate-400">None found</span>
                    ) : (
                      result.matched_skills.map((skill) => (
                        <span key={skill} className="px-2.5 py-1 bg-blue-50 border border-blue-100 text-primary rounded-lg text-xs font-semibold flex items-center">
                          <Check className="mr-1 h-3 w-3" />
                          {skill.toUpperCase()}
                        </span>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Missing Target Skills ({result.missing_skills.length})
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {result.missing_skills.length === 0 ? (
                      <span className="text-sm text-slate-400">None missing</span>
                    ) : (
                      result.missing_skills.map((skill) => (
                        <span key={skill} className="px-2.5 py-1 bg-red-50 border border-red-100 text-red-600 rounded-lg text-xs font-semibold flex items-center">
                          <X className="mr-1 h-3 w-3" />
                          {skill.toUpperCase()}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* XAI and Learning Paths Removed for Recruiter Experience */}

            {/* Generative Interview Questions */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
              <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center">
                <HelpCircle className="mr-2 h-5 w-5 text-indigo-500" />
                Personalized Screening Interview Questions
              </h4>
              
              <div className="space-y-4 custom-scrollbar max-h-72 overflow-y-auto pr-2">
                {result.questions.technical_questions.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      Technical Questions
                    </span>
                    {result.questions.technical_questions.map((q, idx) => (
                      <p key={idx} className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {typeof q === 'string' ? q : (q as any).description || (q as any).question || JSON.stringify(q)}
                      </p>
                    ))}
                  </div>
                )}

                {result.questions.behavioral_questions.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      Behavioral Questions
                    </span>
                    {result.questions.behavioral_questions.map((q, idx) => (
                      <p key={idx} className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {typeof q === 'string' ? q : (q as any).description || (q as any).question || JSON.stringify(q)}
                      </p>
                    ))}
                  </div>
                )}

                {result.questions.technical_questions.length === 0 && result.questions.behavioral_questions.length === 0 && (
                  <p className="text-sm text-slate-400">No screening questions generated.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default Screening;
