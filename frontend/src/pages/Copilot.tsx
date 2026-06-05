import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Candidate, Evaluation } from '../types/candidate';
import { 
  MessageSquare, 
  Mic, 
  HelpCircle, 
  ChevronRight, 
  Award, 
  User,
  CheckCircle,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Search,
  BookOpen
} from 'lucide-react';

interface QuestionsResponse {
  technical_questions: string[];
  behavioral_questions: string[];
}



export const Copilot: React.FC = () => {
  
  // Candidate states
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandId, setSelectedCandId] = useState<number | ''>('');
  
  // Tab 1: Evaluator States
  const [jdText, setJdText] = useState('');
  const [isGeneratingQs, setIsGeneratingQs] = useState(false);
  const [questions, setQuestions] = useState<QuestionsResponse | null>(null);
  
  const [selectedQuestion, setSelectedQuestion] = useState('');
  const [candidateAnswer, setCandidateAnswer] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState<Evaluation | null>(null);
  const [pastEvaluations, setPastEvaluations] = useState<Evaluation[]>([]);
  const [isLoadingPast, setIsLoadingPast] = useState(false);

  const [evalError, setEvalError] = useState('');

  // Initial load: Fetch candidates list
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const response = await api.get<Candidate[]>('/batch/leaderboard');
        setCandidates(response.data);
        if (response.data.length > 0) {
          setSelectedCandId(response.data[0].id);
        }
      } catch (err) {
        console.error('Error fetching candidates:', err);
      }
    };
    fetchCandidates();
  }, []);

  // Fetch past evaluations when candidate selection changes
  useEffect(() => {
    if (!selectedCandId) {
      setPastEvaluations([]);
      setQuestions(null);
      setEvaluationResult(null);
      return;
    }
    
    const fetchPastEvaluations = async () => {
      setIsLoadingPast(true);
      try {
        const response = await api.get<Evaluation[]>(`/copilot/evaluations/${selectedCandId}`);
        setPastEvaluations(response.data);
      } catch (err) {
        console.error('Failed to load past evaluations:', err);
      } finally {
        setIsLoadingPast(false);
      }
    };

    const fetchQuestions = async () => {
      setIsGeneratingQs(true);
      try {
        const response = await api.post<QuestionsResponse>('/copilot/generate-questions', {
          candidate_id: selectedCandId
        });
        setQuestions(response.data);
        if (response.data.technical_questions.length > 0) {
          setSelectedQuestion(response.data.technical_questions[0]);
        } else if (response.data.behavioral_questions.length > 0) {
          setSelectedQuestion(response.data.behavioral_questions[0]);
        }
      } catch (err) {
        console.error('Failed to auto-load questions:', err);
      } finally {
        setIsGeneratingQs(false);
      }
    };

    fetchPastEvaluations();
    fetchQuestions();
  }, [selectedCandId]);

  const handleGenerateQuestions = async () => {
    if (!selectedCandId) return;
    setIsGeneratingQs(true);
    setEvalError('');
    try {
      const response = await api.post<QuestionsResponse>('/copilot/generate-questions', {
        candidate_id: selectedCandId,
        job_description: jdText || undefined
      });
      setQuestions(response.data);
      if (response.data.technical_questions.length > 0) {
        setSelectedQuestion(response.data.technical_questions[0]);
      } else if (response.data.behavioral_questions.length > 0) {
        setSelectedQuestion(response.data.behavioral_questions[0]);
      }
    } catch (err: any) {
      console.error(err);
      setEvalError('Failed to generate customized interview questions.');
    } finally {
      setIsGeneratingQs(false);
    }
  };

  const handleEvaluateAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCandId || !selectedQuestion || !candidateAnswer.trim()) {
      setEvalError('Please select a question and type candidate answer.');
      return;
    }

    setIsEvaluating(true);
    setEvalError('');
    setEvaluationResult(null);

    try {
      const response = await api.post<Evaluation>('/copilot/evaluate', {
        candidate_id: selectedCandId,
        question: selectedQuestion,
        answer: candidateAnswer
      });
      setEvaluationResult(response.data);
      setCandidateAnswer('');
      
      // Refresh past evaluations list
      const pastRes = await api.get<Evaluation[]>(`/copilot/evaluations/${selectedCandId}`);
      setPastEvaluations(pastRes.data);
    } catch (err: any) {
      console.error(err);
      setEvalError('Answer evaluation failed. Please verify credentials.');
    } finally {
      setIsEvaluating(false);
    }
  };

  

  return (
    <div className="space-y-6">
      
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls Panel (Span 1/3) */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Candidate Selection</h3>
              
              {evalError && (
                <div className="rounded-lg bg-red-50 p-4 border border-red-100 text-xs text-red-600">
                  {evalError}
                </div>
              )}

              {/* Selector */}
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Active Candidate Profile</label>
                <select
                  value={selectedCandId}
                  onChange={(e) => {
                    setSelectedCandId(e.target.value ? parseInt(e.target.value) : '');
                    setQuestions(null);
                    setEvaluationResult(null);
                  }}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">-- Choose Candidate --</option>
                  {candidates.map((cand) => (
                    <option key={cand.id} value={cand.id}>
                      {cand.name} ({cand.prediction})
                    </option>
                  ))}
                </select>
              </div>

              {/* Custom JD */}
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Job Context (Optional)</label>
                <textarea
                  rows={3}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste context requirements for custom question generation..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-slate-700 text-xs focus:outline-none focus:ring-2 focus:ring-primary/20 custom-scrollbar"
                />
              </div>

              <button
                type="button"
                onClick={handleGenerateQuestions}
                disabled={isGeneratingQs || !selectedCandId}
                className="w-full bg-primary hover:bg-primary-hover text-white py-2 rounded-lg font-semibold text-xs transition disabled:opacity-50 flex items-center justify-center shadow-sm"
              >
                {isGeneratingQs ? (
                  <>
                    <RefreshCw className="animate-spin mr-2 h-4 w-4" />
                    Generating Questions...
                  </>
                ) : (
                  'Generate Custom Questions'
                )}
              </button>
            </div>

            {/* Questions lists if generated */}
            {questions && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4 max-h-[350px] overflow-y-auto custom-scrollbar">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider border-b border-slate-100 pb-2">Generated Questions</h4>
                
                {/* Tech list */}
                {questions.technical_questions.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-wider block">Technical Assessment</span>
                    {questions.technical_questions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedQuestion(q)}
                        className={`w-full text-left text-xs p-2.5 rounded-lg border transition text-slate-600 block ${
                          selectedQuestion === q 
                            ? 'bg-indigo-50/50 border-indigo-200 font-medium text-slate-800' 
                            : 'border-slate-100 hover:bg-slate-50'
                        }`}
                      >
                        {typeof q === 'string' ? q : (q as any).description || (q as any).question || JSON.stringify(q)}
                      </button>
                    ))}
                  </div>
                )}

                {/* Behavioral list */}
                {questions.behavioral_questions.length > 0 && (
                  <div className="space-y-2 mt-4">
                    <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider block">Behavioral Assessment</span>
                    {questions.behavioral_questions.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedQuestion(q)}
                        className={`w-full text-left text-xs p-2.5 rounded-lg border transition text-slate-600 block ${
                          selectedQuestion === q 
                            ? 'bg-emerald-50/50 border-emerald-200 font-medium text-slate-800' 
                            : 'border-slate-100 hover:bg-slate-50'
                        }`}
                      >
                        {typeof q === 'string' ? q : (q as any).description || (q as any).question || JSON.stringify(q)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Assessment workspace and logs (Span 2/3) */}
          <div className="lg:col-span-2 space-y-6">
            {!selectedCandId ? (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 flex flex-col items-center justify-center text-center h-full min-h-[400px]">
                <div className="bg-slate-100 p-4 rounded-full mb-4">
                  <User className="h-8 w-8 text-slate-400" />
                </div>
                <h3 className="text-base font-bold text-slate-700 mb-1">No candidate selected</h3>
                <p className="text-slate-400 text-sm">Choose a candidate from the left panel to load their interview questions and begin evaluation.</p>
              </div>
            ) : (
              <>
            {/* Input answer evaluator */}
            {selectedQuestion && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Evaluation Workspace</h3>
                
                <div className="p-3 bg-slate-50 border border-slate-100 rounded-lg text-xs font-semibold text-slate-600">
                  <HelpCircle className="inline-block mr-1.5 h-4 w-4 text-indigo-500" />
                  {typeof selectedQuestion === 'string' ? selectedQuestion : (selectedQuestion as any).description || (selectedQuestion as any).question || JSON.stringify(selectedQuestion)}
                </div>

                <form onSubmit={handleEvaluateAnswer} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Candidate Verbal/Typed Response</label>
                    <textarea
                      required
                      rows={5}
                      value={candidateAnswer}
                      onChange={(e) => setCandidateAnswer(e.target.value)}
                      placeholder="Paste or type candidate response here..."
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition custom-scrollbar"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isEvaluating}
                    className="w-full bg-primary hover:bg-primary-hover text-white py-2 rounded-lg font-bold text-xs transition disabled:opacity-50 shadow-sm"
                  >
                    {isEvaluating ? 'Assessing Answer Performance...' : 'Submit Evaluation'}
                  </button>
                </form>
              </div>
            )}

            {/* Evaluation Score Result Panel */}
            {evaluationResult && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6 animate-fade-in">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <h4 className="font-bold text-slate-800 text-base">Answer Evaluation Metrics</h4>
                  <div className="flex items-center space-x-1">
                    <Award className="h-5 w-5 text-indigo-600" />
                    <span className="text-xl font-extrabold text-indigo-600">{evaluationResult.score} / 10</span>
                  </div>
                </div>

                {/* Indicators Row */}
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-slate-50/50 border border-slate-100 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Technical Depth</span>
                    <p className="text-lg font-bold text-slate-700 mt-1">{evaluationResult.technical_depth} / 10</p>
                  </div>
                  <div className="p-3 bg-slate-50/50 border border-slate-100 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Communication</span>
                    <p className="text-lg font-bold text-slate-700 mt-1">{evaluationResult.communication} / 10</p>
                  </div>
                  <div className="p-3 bg-slate-50/50 border border-slate-100 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Completeness</span>
                    <p className="text-lg font-bold text-slate-700 mt-1">{evaluationResult.completeness} / 10</p>
                  </div>
                </div>

                {/* Strengths & Improvements Lists */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  <div className="space-y-2.5">
                    <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">Strengths Highlights</span>
                    {evaluationResult.strengths.map((str, idx) => (
                      <div key={idx} className="flex items-start text-xs text-slate-600 bg-emerald-50/20 p-2.5 rounded-lg border border-emerald-100/50">
                        <CheckCircle className="h-4 w-4 text-emerald-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span>{str}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="space-y-2.5">
                    <span className="text-xs font-semibold text-amber-500 uppercase tracking-wider block">Areas for Improvement</span>
                    {evaluationResult.improvements.map((imp, idx) => (
                      <div key={idx} className="flex items-start text-xs text-slate-600 bg-amber-50/20 p-2.5 rounded-lg border border-amber-100/50">
                        <AlertCircle className="h-4 w-4 text-amber-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span>{imp}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Past Evaluations Logs */}
            {selectedCandId && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Historical Evaluation Records</h3>
                
                {isLoadingPast ? (
                  <div className="flex justify-center py-6">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
                  </div>
                ) : pastEvaluations.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-6">No previous questions evaluated for this candidate.</p>
                ) : (
                  <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto custom-scrollbar pr-2 space-y-4">
                    {pastEvaluations.map((ev) => (
                      <div key={ev.id} className="pt-4 first:pt-0 space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-slate-800">Q: {ev.question}</span>
                          <span className="font-semibold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
                            Score: {ev.score}/10
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 italic">Answer: "{ev.answer}"</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
              </>
            )}
          </div>
        </div>
      
    </div>
  );
};
export default Copilot;
