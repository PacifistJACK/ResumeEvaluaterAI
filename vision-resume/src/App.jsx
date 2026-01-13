import { Upload, FileText, ThumbsUp, ThumbsDown, Lightbulb, RotateCcw, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import React, { useState, useRef, useEffect } from 'react';

const App = () => {
  useEffect(() => {
  const PING_INTERVAL = 5 * 60 * 1000; // 5 minutes

  const pingBackend = () => {
    fetch("https://resumeevaluaterai.onrender.com/health")
      .then(() => console.log("Backend pinged 🗿"))
      .catch(err => console.error("Ping failed:", err));
  };

  // Initial ping on load
  pingBackend();

  const interval = setInterval(pingBackend, PING_INTERVAL);

  return () => clearInterval(interval);
}, []);

  const [currentPage, setCurrentPage] = useState('upload');
  const [resumeFile, setResumeFile] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false); // Added for loading state
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setResumeFile(file);
      setIsAnalyzing(true); // Start loading

      const formData = new FormData();
      formData.append("file", file);

      try {
        // --- REAL BACKEND CONNECTION ---
        // Change this in your App.js
        const response = await fetch("https://resumeevaluaterai.onrender.com/analyze", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Backend connection failed");
        }

        const data = await response.json();
        setEvaluation(data);
        setCurrentPage('result');
      } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to the AI server. Is your Python backend running?");
        setResumeFile(null); // Reset on error
      } finally {
        setIsAnalyzing(false); // Stop loading
      }
    } else {
      alert("Please upload a PDF file.");
    }
  };

  const resetEvaluator = () => {
    setResumeFile(null);
    setEvaluation(null);
    setCurrentPage('upload');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreBg = (score) => {
    if (score >= 85) return 'bg-green-500';
    if (score >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden text-white font-sans">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full opacity-10"
            style={{
              background: `radial-gradient(circle, ${i % 3 === 0 ? '#8B5CF6' : i % 3 === 1 ? '#3B82F6' : '#EC4899'}, transparent)`,
              width: Math.random() * 200 + 100,
              height: Math.random() * 200 + 100,
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
            }}
            animate={{
              x: [0, Math.random() * 100 - 50],
              y: [0, Math.random() * 100 - 50],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: Math.random() * 10 + 10,
              repeat: Infinity,
              repeatType: "reverse",
            }}
          />
        ))}
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 flex flex-col min-h-screen">
        {/* Header */}
        <header className="flex items-center justify-between mb-12">
          <div className="flex items-center space-x-2">
            <FileText className="w-8 h-8 text-blue-400" />
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              ResumeAI
            </span>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-grow flex items-center justify-center">
          {currentPage === 'upload' ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full max-w-2xl"
            >
              <div className="text-center mb-10">
                <h1 className="text-5xl font-bold mb-6 leading-tight">
                  Unlock Your Resume's <br />
                  <span className="text-blue-400">Full Potential</span>
                </h1>
                <p className="text-xl text-gray-300">
                  Get instant AI-powered feedback to land your dream job.
                </p>
              </div>

              <motion.div
                whileHover={{ scale: 1.02 }}
                className="bg-white/10 backdrop-blur-lg rounded-3xl p-12 border-2 border-dashed border-white/20 text-center cursor-pointer hover:bg-white/15 transition-all relative"
                onClick={() => !isAnalyzing && fileInputRef.current.click()}
              >
                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  disabled={isAnalyzing}
                />

                {isAnalyzing ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="w-16 h-16 text-blue-400 animate-spin mb-4" />
                    <h3 className="text-2xl font-semibold mb-2">Analyzing...</h3>
                    <p className="text-gray-400">Reading your resume structure</p>
                  </div>
                ) : (
                  <>
                    <div className="w-20 h-20 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                      <Upload className="w-10 h-10 text-blue-400" />
                    </div>
                    <h3 className="text-2xl font-semibold mb-2">Upload Resume</h3>
                    <p className="text-gray-400 mb-6">PDF files only (Max 10MB)</p>
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-full font-semibold transition-colors shadow-lg shadow-blue-600/30">
                      Select File
                    </button>
                  </>
                )}
              </motion.div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="w-full max-w-4xl"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Score Card */}
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/10 flex flex-col items-center justify-center text-center md:col-span-1"
                >
                  <h2 className="text-xl text-gray-300 mb-4">Resume Score</h2>
                  <div className={`text-7xl font-bold mb-2 ${getScoreColor(evaluation.score)}`}>
                    {evaluation.score}
                  </div>
                  <div className={`h-2 w-full rounded-full bg-gray-700 overflow-hidden`}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${evaluation.score}%` }}
                      transition={{ duration: 1, delay: 0.5 }}
                      className={`h-full ${getScoreBg(evaluation.score)}`}
                    />
                  </div>
                </motion.div>

                {/* Recommendations */}
                <motion.div
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/10 md:col-span-2"
                >
                  <div className="flex items-center mb-6">
                    <Lightbulb className="w-6 h-6 text-yellow-400 mr-3" />
                    <h3 className="text-2xl font-semibold">Key Recommendations</h3>
                  </div>
                  <ul className="space-y-4">
                    {evaluation.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start bg-white/5 p-3 rounded-xl">
                        <span className="w-6 h-6 rounded-full bg-yellow-500/20 text-yellow-400 flex items-center justify-center mr-3 text-sm flex-shrink-0">
                          {index + 1}
                        </span>
                        <span className="text-gray-300">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths */}
                <motion.div
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/10"
                >
                  <div className="flex items-center mb-6">
                    <ThumbsUp className="w-6 h-6 text-green-400 mr-3" />
                    <h3 className="text-xl font-semibold text-green-400">Strengths</h3>
                  </div>
                  <ul className="space-y-3">
                    {evaluation.goodPoints?.map((item, index) => (
                      <li key={index} className="flex items-start">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 mt-2 mr-3" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    )) || evaluation.strengths?.map((item, index) => (
                      <li key={index} className="flex items-start">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400 mt-2 mr-3" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    ))}
                  </ul>
                </motion.div>

                {/* Weaknesses */}
                <motion.div
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/10"
                >
                  <div className="flex items-center mb-6">
                    <ThumbsDown className="w-6 h-6 text-red-400 mr-3" />
                    <h3 className="text-xl font-semibold text-red-400">Improvements</h3>
                  </div>
                  <ul className="space-y-3">
                    {evaluation.badPoints?.map((item, index) => (
                      <li key={index} className="flex items-start">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 mr-3" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    )) || evaluation.weaknesses?.map((item, index) => (
                      <li key={index} className="flex items-start">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-2 mr-3" />
                        <span className="text-gray-300">{item}</span>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              </div>

              <div className="mt-8 flex justify-center">
                <button
                  onClick={resetEvaluator}
                  className="flex items-center space-x-2 bg-white/10 hover:bg-white/20 text-white px-8 py-3 rounded-full font-semibold transition-all backdrop-blur-lg border border-white/20"
                >
                  <RotateCcw className="w-5 h-5" />
                  <span>Analyze Another Resume</span>
                </button>
              </div>
            </motion.div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;