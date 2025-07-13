import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Search, 
  FileText, 
  MessageSquare, 
  TrendingUp, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Zap,
  Brain,
  Shield,
  Database,
  Send,
  Loader2,
  Clock,
  Users,
  Activity
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [stats, setStats] = useState({});
  const [documents, setDocuments] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);

  useEffect(() => {
    // Generate session ID on mount
    setSessionId(Date.now().toString());
    
    // Fetch initial data
    fetchStats();
    fetchDocuments();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/query`, {
        query: query.trim(),
        session_id: sessionId
      });
      
      const newResult = {
        id: Date.now(),
        query: query.trim(),
        ...response.data,
        timestamp: new Date().toISOString()
      };
      
      setResults(prev => [newResult, ...prev]);
      setQuery('');
      setSelectedResult(newResult);
      
      // Update stats
      fetchStats();
    } catch (error) {
      console.error('Error processing query:', error);
      const errorResult = {
        id: Date.now(),
        query: query.trim(),
        decision: 'error',
        justification: 'An error occurred while processing your query. Please try again.',
        confidence_score: 0,
        referenced_clauses: [],
        timestamp: new Date().toISOString()
      };
      setResults(prev => [errorResult, ...prev]);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIcon = (decision) => {
    switch (decision) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getDecisionColor = (decision) => {
    switch (decision) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };

  const formatAmount = (amount) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">HackRx 6.0</h1>
                <p className="text-sm text-gray-600">LLM Query Retrieval System</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Session: {sessionId?.slice(-6)}
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600">System Active</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-12 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.h2 
              className="text-4xl font-bold text-white mb-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              Intelligent Insurance Query Processing
            </motion.h2>
            <motion.p 
              className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              Process natural language queries and retrieve relevant information from policy documents using advanced LLM technology
            </motion.p>
            
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="flex items-center justify-center mb-2">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-white">{stats.total_documents || 0}</div>
                <div className="text-sm text-blue-100">Documents</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="flex items-center justify-center mb-2">
                  <MessageSquare className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-white">{stats.total_queries || 0}</div>
                <div className="text-sm text-blue-100">Queries</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="flex items-center justify-center mb-2">
                  <Users className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-white">{stats.total_sessions || 0}</div>
                <div className="text-sm text-blue-100">Sessions</div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                <div className="flex items-center justify-center mb-2">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-white">{stats.system_status === 'operational' ? 'Online' : 'Offline'}</div>
                <div className="text-sm text-blue-100">Status</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Query Input */}
          <div className="lg:col-span-2">
            <motion.div 
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Search className="w-5 h-5 mr-2" />
                Submit Query
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Natural Language Query
                  </label>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., 46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="4"
                    disabled={loading}
                  />
                </div>
                
                <div className="flex items-center space-x-4">
                  <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4 mr-2" />
                    )}
                    {loading ? 'Processing...' : 'Process Query'}
                  </button>
                  
                  <div className="text-sm text-gray-500">
                    Powered by free LLM models
                  </div>
                </div>
              </form>
            </motion.div>

            {/* Results */}
            <div className="space-y-4">
              <AnimatePresence>
                {results.map((result) => (
                  <motion.div
                    key={result.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 cursor-pointer transition-all hover:shadow-md ${
                      selectedResult?.id === result.id ? 'ring-2 ring-blue-500' : ''
                    }`}
                    onClick={() => setSelectedResult(result)}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        {getDecisionIcon(result.decision)}
                        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getDecisionColor(result.decision)}`}>
                          {result.decision.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center">
                          <TrendingUp className="w-4 h-4 mr-1" />
                          {(result.confidence_score * 100).toFixed(1)}%
                        </div>
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {result.processing_time ? `${result.processing_time.toFixed(2)}s` : 'N/A'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="mb-3">
                      <h4 className="font-medium text-gray-900 mb-1">Query:</h4>
                      <p className="text-gray-700 text-sm">{result.query}</p>
                    </div>
                    
                    {result.amount && (
                      <div className="mb-3">
                        <h4 className="font-medium text-gray-900 mb-1">Amount:</h4>
                        <p className="text-lg font-bold text-green-600">{formatAmount(result.amount)}</p>
                      </div>
                    )}
                    
                    <div className="mb-3">
                      <h4 className="font-medium text-gray-900 mb-1">Justification:</h4>
                      <p className="text-gray-700 text-sm whitespace-pre-line">{result.justification}</p>
                    </div>
                    
                    {result.referenced_clauses && result.referenced_clauses.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-1">Referenced Documents:</h4>
                        <div className="space-y-1">
                          {result.referenced_clauses.map((clause, index) => (
                            <div key={index} className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                              <div className="font-medium">{clause.document}</div>
                              <div className="text-gray-500">Relevance: {(clause.relevance_score * 100).toFixed(1)}%</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {results.length === 0 && (
                <div className="text-center py-12">
                  <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No queries yet</h3>
                  <p className="text-gray-600">Submit your first query to get started</p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Features */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Zap className="w-5 h-5 text-blue-500" />
                  <span className="text-sm text-gray-700">Real-time Processing</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Brain className="w-5 h-5 text-purple-500" />
                  <span className="text-sm text-gray-700">Advanced LLM Analysis</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-green-500" />
                  <span className="text-sm text-gray-700">Secure Processing</span>
                </div>
                <div className="flex items-center space-x-3">
                  <Database className="w-5 h-5 text-indigo-500" />
                  <span className="text-sm text-gray-700">Document Retrieval</span>
                </div>
              </div>
            </div>

            {/* Documents */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Documents</h3>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-700 truncate">{doc.name}</span>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${doc.processed ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                  </div>
                ))}
              </div>
            </div>

            {/* Example Queries */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Example Queries</h3>
              <div className="space-y-3">
                <button
                  onClick={() => setQuery('46-year-old male, knee surgery in Pune, 3-month-old insurance policy')}
                  className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="text-sm text-gray-700">46-year-old male, knee surgery in Pune, 3-month-old insurance policy</div>
                </button>
                <button
                  onClick={() => setQuery('Female, 35 years, heart surgery, 2-year policy')}
                  className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="text-sm text-gray-700">Female, 35 years, heart surgery, 2-year policy</div>
                </button>
                <button
                  onClick={() => setQuery('Cancer treatment, Mumbai, 1-year policy duration')}
                  className="w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="text-sm text-gray-700">Cancer treatment, Mumbai, 1-year policy duration</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;