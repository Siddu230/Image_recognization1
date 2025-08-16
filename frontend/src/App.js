import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Upload, Image as ImageIcon, Eye, Trash2, Clock, Sparkles, Brain } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');

  // Fetch analysis history on component mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/analysis-history`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setAnalysisResult(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data:image/jpeg;base64, prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
    });
  };

  const analyzeImage = async () => {
    if (!selectedFile) return;

    setAnalyzing(true);
    try {
      const base64 = await convertFileToBase64(selectedFile);
      
      const response = await axios.post(`${API}/analyze-image`, {
        filename: selectedFile.name,
        image_base64: base64
      });

      setAnalysisResult(response.data);
      setActiveTab('result');
      await fetchHistory(); // Refresh history
    } catch (error) {
      console.error('Error analyzing image:', error);
      alert('Failed to analyze image. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const deleteAnalysis = async (id) => {
    try {
      await axios.delete(`${API}/analysis/${id}`);
      await fetchHistory();
      if (analysisResult && analysisResult.id === id) {
        setAnalysisResult(null);
      }
    } catch (error) {
      console.error('Error deleting analysis:', error);
      alert('Failed to delete analysis');
    }
  };

  const viewAnalysis = (analysis) => {
    setAnalysisResult(analysis);
    setActiveTab('result');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">PicoGnize</h1>
                <p className="text-sm text-gray-600">AI-Powered Image Recognition</p>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Upload className="inline h-4 w-4 mr-2" />
                Upload
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'history'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Clock className="inline h-4 w-4 mr-2" />
                History
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="space-y-8">
            {/* Upload Area */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                Upload Image for Analysis
              </h2>
              
              {!selectedFile ? (
                <div
                  className={`border-3 border-dashed rounded-xl p-12 text-center transition-all ${
                    dragOver
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <ImageIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                  <p className="text-xl font-medium text-gray-700 mb-2">
                    Drop your image here or click to upload
                  </p>
                  <p className="text-gray-500 mb-6">
                    Supports JPEG, PNG, GIF, and WebP formats
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileSelect(e.target.files[0])}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all cursor-pointer"
                  >
                    <Upload className="h-5 w-5 mr-2" />
                    Select Image
                  </label>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="flex items-center justify-center">
                    <img
                      src={URL.createObjectURL(selectedFile)}
                      alt="Selected"
                      className="max-h-96 max-w-full rounded-xl shadow-lg"
                    />
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-medium text-gray-700 mb-4">
                      {selectedFile.name}
                    </p>
                    <div className="flex justify-center space-x-4">
                      <button
                        onClick={analyzeImage}
                        disabled={analyzing}
                        className={`inline-flex items-center px-8 py-3 font-medium rounded-lg transition-all ${
                          analyzing
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-gradient-to-r from-green-500 to-blue-500 text-white hover:from-green-600 hover:to-blue-600'
                        }`}
                      >
                        {analyzing ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-5 w-5 mr-2" />
                            Analyze Image
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'result' && analysisResult && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Analysis Results</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Image */}
              <div>
                <img
                  src={`data:image/jpeg;base64,${analysisResult.image_base64}`}
                  alt={analysisResult.filename}
                  className="w-full rounded-xl shadow-lg"
                />
                <p className="text-center text-gray-600 mt-2 font-medium">
                  {analysisResult.filename}
                </p>
              </div>

              {/* Analysis Details */}
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Overall Description</h3>
                  <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg">
                    {analysisResult.analysis.split('\n').find(line => line.startsWith('DESCRIPTION:'))?.replace('DESCRIPTION:', '').trim() || 'No description available'}
                  </p>
                </div>

                {analysisResult.objects_detected?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Objects Detected</h3>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.objects_detected.map((object, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                        >
                          {object}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.text_found && analysisResult.text_found !== "None detected" && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Text Found</h3>
                    <p className="text-gray-700 bg-yellow-50 p-3 rounded-lg font-mono">
                      "{analysisResult.text_found}"
                    </p>
                  </div>
                )}

                {analysisResult.emotions?.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Emotions Detected</h3>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.emotions.map((emotion, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-pink-100 text-pink-800 rounded-full text-sm font-medium"
                        >
                          {emotion}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.scene_description && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Scene Context</h3>
                    <p className="text-gray-700 bg-green-50 p-3 rounded-lg">
                      {analysisResult.scene_description}
                    </p>
                  </div>
                )}

                {analysisResult.confidence && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Confidence Level</h3>
                    <span className={`px-4 py-2 rounded-lg font-medium ${
                      analysisResult.confidence.toLowerCase() === 'high' 
                        ? 'bg-green-100 text-green-800'
                        : analysisResult.confidence.toLowerCase() === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {analysisResult.confidence}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Analysis History</h2>
            
            {history.length === 0 ? (
              <div className="text-center py-12">
                <ImageIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                <p className="text-xl text-gray-600">No analyses yet</p>
                <p className="text-gray-500">Upload your first image to get started!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {history.map((analysis) => (
                  <div key={analysis.id} className="border rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
                    <img
                      src={`data:image/jpeg;base64,${analysis.image_base64}`}
                      alt={analysis.filename}
                      className="w-full h-48 object-cover"
                    />
                    <div className="p-4">
                      <h3 className="font-medium text-gray-900 mb-2 truncate">
                        {analysis.filename}
                      </h3>
                      <p className="text-sm text-gray-600 mb-3">
                        {new Date(analysis.timestamp).toLocaleDateString()}
                      </p>
                      <div className="flex justify-between">
                        <button
                          onClick={() => viewAnalysis(analysis)}
                          className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </button>
                        <button
                          onClick={() => deleteAnalysis(analysis.id)}
                          className="flex items-center text-red-600 hover:text-red-800 transition-colors"
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;