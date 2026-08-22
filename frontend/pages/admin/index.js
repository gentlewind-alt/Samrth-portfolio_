import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

export default function AdminDashboard() {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [filterText, setFilterText] = useState('');
  const fileInputRef = useRef(null);

  const API_URL = '/api';

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/resumes/`);
      if (!res.ok) throw new Error('Failed to fetch resumes from API');
      const data = await res.json();
      // Sort resumes by upload time (newest first)
      data.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
      setResumes(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Could not connect to the backend server. Make sure it is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeydown = (e) => {
      // Ctrl/Cmd + U to focus upload
      if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        fileInputRef.current?.click();
      }
      // Ctrl/Cmd + R to refresh
      if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        fetchResumes();
      }
    };
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, []);

  const handleUploadFile = async (file) => {
    if (!file) return;
    if (file.type !== 'application/pdf') {
      alert('Only PDF files are supported.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      const res = await fetch(`${API_URL}/resumes/`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Upload failed');
      
      const newResume = await res.json();
      setResumes((prev) => [newResume, ...prev]);
      alert('Resume uploaded and processed successfully!');
    } catch (err) {
      console.error(err);
      alert('Error uploading file. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleUploadFile(e.target.files[0]);
    }
  };

  const handleDeleteResume = async (id) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      const res = await fetch(`${API_URL}/resumes/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Delete failed');
      setResumes((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      console.error(err);
      alert('Failed to delete resume. Please try again.');
    }
  };

  const formatDate = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] px-4 py-8 md:px-8 max-w-6xl mx-auto">
      {/* Header */}
      <header className="mb-12 text-center md:text-left flex flex-col md:flex-row justify-between items-center border-b border-[#21262d] pb-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-[#58a6ff] to-[#bc8cff] bg-clip-text text-transparent">
            Resume CMS Platform
          </h1>
          <p className="text-gray-400 mt-2">Deterministic Resume Parsing & Controlled CMS Editor</p>
        </div>
        <div className="flex gap-4">
          <Link href="/" className="px-4 py-2 bg-[#21262d] border border-[#30363d] hover:bg-[#30363d] rounded-md transition text-sm flex items-center gap-2">
            View Live Site
          </Link>
          <button 
            onClick={fetchResumes}
            className="px-4 py-2 bg-[#21262d] border border-[#30363d] hover:bg-[#30363d] rounded-md transition text-sm flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.228 15.116" />
            </svg>
            Refresh List
          </button>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Column (1 Span) */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 shadow-xl">
            <h2 className="text-xl font-bold mb-4 text-[#58a6ff]">Upload PDF Resume</h2>
            <p className="text-xs text-gray-400 mb-6">
              PDF resumes will be extracted deterministically using layout splitting and loaded into the database schema.
            </p>

            {/* Dropzone */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition cursor-pointer relative ${
                dragActive
                  ? 'border-[#58a6ff] bg-[#1f2937]'
                  : 'border-[#30363d] hover:border-[#8b949e] bg-[#0d1117]'
              }`}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                id="file-upload"
                accept="application/pdf"
                className="hidden"
                onChange={handleFileInput}
                disabled={uploading}
              />
              <label htmlFor="file-upload" className="cursor-pointer block w-full h-full">
                {uploading ? (
                  <div className="space-y-3">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#58a6ff] mx-auto"></div>
                    <div>
                      <p className="text-sm font-medium text-gray-300">Parsing Resume PDF...</p>
                      {uploadProgress > 0 && (
                        <div className="mt-2 bg-[#1f2937] rounded-full h-1.5">
                          <div
                            className="bg-[#58a6ff] h-1.5 rounded-full transition-all"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <svg className="w-12 h-12 mx-auto text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <div>
                      <p className="text-sm font-semibold text-[#58a6ff]">Click to upload</p>
                      <p className="text-xs text-gray-400 mt-1">or drag and drop PDF here</p>
                      <p className="text-xs text-gray-500 mt-2"><kbd className="px-1.5 py-0.5 bg-[#1f2937] rounded text-[10px] border border-[#30363d]">Ctrl+U</kbd> to upload</p>
                    </div>
                  </div>
                )}
              </label>
            </div>
          </div>

          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6">
            <h3 className="font-bold text-sm text-[#bc8cff] mb-2">MVP Phase Status</h3>
            <ul className="text-xs space-y-2 text-gray-400">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span>FastAPI Backend Setup</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span>Deterministic Text Extraction</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span>Next.js Dashboard & List</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span>Verification & Edit Workspace</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Resumes List Column (2 Spans) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 shadow-xl min-h-[400px]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div className="flex-1">
                <h2 className="text-xl font-bold">Parsed Resumes</h2>
                <p className="text-xs text-gray-400 mt-1">Manage and edit your resume versions</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs px-3 py-1 bg-[#21262d] border border-[#30363d] text-gray-400 rounded-full font-medium">
                  {resumes.filter(r => r.filename.toLowerCase().includes(filterText.toLowerCase())).length} of {resumes.length}
                </span>
                <button
                  onClick={fetchResumes}
                  title="Refresh list (Ctrl+R)"
                  className="p-2 text-gray-400 hover:text-white hover:bg-[#21262d] rounded-md transition text-sm"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.228 15.116" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Search Bar */}
            <div className="mb-6">
              <input
                type="text"
                placeholder="Search resumes by filename..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#58a6ff] transition"
              />
            </div>

            {error && (
              <div className="bg-red-950 border border-red-800 text-red-300 px-4 py-3 rounded-lg text-sm mb-6">
                {error}
              </div>
            )}

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-3">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#bc8cff]"></div>
                <p className="text-sm text-gray-400">Loading resumes...</p>
              </div>
            ) : resumes.filter(r => r.filename.toLowerCase().includes(filterText.toLowerCase())).length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-[#30363d] rounded-lg">
                <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-lg font-semibold text-gray-400">{filterText ? 'No matching resumes' : 'No resumes found'}</p>
                <p className="text-xs text-gray-500 mt-1">{filterText ? 'Try adjusting your search.' : 'Upload a resume PDF to get started.'}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {resumes.filter(r => r.filename.toLowerCase().includes(filterText.toLowerCase())).map((resume) => (
                  <div 
                    key={resume.id} 
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-[#0d1117] border border-[#30363d] rounded-lg hover:border-[#8b949e] transition gap-4"
                  >
                    <div className="flex items-center space-x-4 min-w-0">
                      <div className="p-3 bg-[#1f2937] rounded-lg text-[#58a6ff] flex-shrink-0">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-bold text-base truncate text-[#c9d1d9]">{resume.filename}</h3>
                        <p className="text-xs text-gray-400 mt-0.5">Uploaded {formatDate(resume.uploaded_at)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 self-end sm:self-center flex-wrap justify-end">
                      <button
                        onClick={() => {
                          const url = `/api/resumes/${resume.id}/pdf`;
                          navigator.clipboard.writeText(window.location.origin + url);
                          alert('PDF URL copied to clipboard!');
                        }}
                        className="px-3 py-2 text-xs font-semibold text-gray-400 hover:text-white hover:bg-[#21262d] border border-[#30363d] rounded-md transition"
                        title="Copy PDF download link"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                      <Link
                        href={`/resumes/${resume.id}`}
                        className="px-4 py-2 text-xs font-semibold text-white bg-[#238636] hover:bg-[#2ea043] rounded-md transition text-center"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => handleDeleteResume(resume.id)}
                        className="px-4 py-2 text-xs font-semibold text-[#f85149] hover:text-white hover:bg-[#da3633] border border-[#f85149] hover:border-transparent rounded-md transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
