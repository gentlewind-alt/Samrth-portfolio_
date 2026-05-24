import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';

export default function ResumeEditor() {
  const router = useRouter();
  const { id } = router.query;
  
  const API_URL = '/api';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [leftPaneTab, setLeftPaneTab] = useState('pdf');
  const [resumeData, setResumeData] = useState({
    filename: '',
    content_json: {
      name: '',
      address: '',
      email: '',
      number: '',
      links: '',
      description: { headline: 'Profile Summary', body: '' },
      experience: { headline: 'Work Experience', body: '' },
      project: { headline: 'Key Projects', body: '' },
      education: { headline: 'Academic Education', body: '' },
      skills: { headline: 'Core Skills', body: '' },
      strengths: { headline: 'Strengths', body: '' },
      hobbies: { headline: 'Hobbies & Interests', body: '' },
      status: { headline: 'Employment Status', body: '' },
      focus: { headline: 'Career Focus', body: '' },
      availability: { headline: 'Availability', body: '' }
    }
  });

  const sectionsConfig = [
    { key: 'description', label: 'Profile Summary', rows: 4 },
    { key: 'experience', label: 'Work Experience', rows: 6 },
    { key: 'project', label: 'Key Projects', rows: 6 },
    { key: 'education', label: 'Academic Education', rows: 4 },
    { key: 'skills', label: 'Core Skills', rows: 4 },
    { key: 'strengths', label: 'Strengths & Competencies', rows: 4 },
    { key: 'hobbies', label: 'Hobbies & Interests', rows: 4 },
    { key: 'status', label: 'Employment Status', rows: 2 },
    { key: 'focus', label: 'Career Focus', rows: 2 },
    { key: 'availability', label: 'Availability', rows: 2 },
  ];

  useEffect(() => {
    if (!id) return;

    const fetchResume = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_URL}/resumes/${id}`);
        if (!res.ok) throw new Error('Failed to load resume details.');
        const data = await res.json();
        
        const content = data.content_json || {};
        
        // Map from old or new structure to ensure backward compatibility
        const safeData = {
          filename: data.filename || '',
          content_json: {
            name: content.name || content.personal?.name || '',
            address: content.address || content.personal?.location || '',
            email: content.email || content.personal?.email || '',
            number: content.number || content.personal?.phone || '',
            links: Array.isArray(content.links) ? content.links.join(', ') : (content.links || ''),
            description: {
              headline: content.description?.headline || 'Profile Summary',
              body: content.description?.body || content.summary || ''
            },
            experience: {
              headline: content.experience?.headline || 'Work Experience',
              body: content.experience?.body || content.experience || ''
            },
            project: {
              headline: content.project?.headline || 'Key Projects',
              body: content.project?.body || content.projects || ''
            },
            education: {
              headline: content.education?.headline || 'Academic Education',
              body: content.education?.body || content.education || ''
            },
            skills: {
              headline: content.skills?.headline || 'Core Skills',
              body: content.skills?.body || content.skills || ''
            },
            strengths: {
              headline: content.strengths?.headline || 'Strengths',
              body: content.strengths?.body || ''
            },
            hobbies: {
              headline: content.hobbies?.headline || 'Hobbies & Interests',
              body: content.hobbies?.body || ''
            },
            status: {
              headline: content.status?.headline || 'Employment Status',
              body: content.status?.body || ''
            },
            focus: {
              headline: content.focus?.headline || 'Career Focus',
              body: content.focus?.body || ''
            },
            availability: {
              headline: content.availability?.headline || 'Availability',
              body: content.availability?.body || ''
            }
          }
        };

        setResumeData(safeData);
        setError(null);
      } catch (err) {
        console.error(err);
        setError('Error loading resume. Make sure the backend server is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchResume();
  }, [id]);

  const handleMetadataChange = (field, val) => {
    setResumeData(prev => ({
      ...prev,
      content_json: {
        ...prev.content_json,
        [field]: val
      }
    }));
  };

  const handleSectionChange = (sectionKey, part, val) => {
    setResumeData(prev => ({
      ...prev,
      content_json: {
        ...prev.content_json,
        [sectionKey]: {
          ...prev.content_json[sectionKey],
          [part]: val
        }
      }
    }));
  };

  const handleSaveChanges = async (e) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      setSaveSuccess(false);

      // Convert links string back to an array
      const processedLinks = typeof resumeData.content_json.links === 'string'
        ? resumeData.content_json.links.split(',').map(s => s.trim()).filter(Boolean)
        : resumeData.content_json.links;

      const payload = {
        ...resumeData.content_json,
        links: processedLinks
      };

      const res = await fetch(`${API_URL}/resumes/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Save failed');
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error(err);
      alert('Failed to save changes. Please check server logs.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex flex-col items-center justify-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#58a6ff]"></div>
        <p className="text-gray-400">Loading workspace...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0d1117] flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-red-950 border border-red-800 text-red-300 p-6 rounded-xl max-w-md">
          <h2 className="text-lg font-bold mb-2">Error</h2>
          <p className="text-sm mb-4">{error}</p>
          <Link href="/admin" className="px-4 py-2 bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] rounded-md transition text-xs font-semibold">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0d1117] text-[#c9d1d9] flex flex-col">
      {/* Workspace Header */}
      <header className="h-16 border-b border-[#21262d] bg-[#161b22] px-6 flex justify-between items-center flex-shrink-0">
        <div className="flex items-center space-x-4 min-w-0">
          <Link href="/admin" className="p-2 hover:bg-[#21262d] rounded-lg transition text-gray-400 hover:text-white">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="min-w-0">
            <h1 className="font-bold text-sm text-[#58a6ff] truncate">Verify & Edit Workspace</h1>
            <p className="text-xs text-gray-400 truncate">{resumeData.filename}</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {saveSuccess && (
            <span className="text-xs font-semibold text-green-400 bg-green-950/50 border border-green-800 px-3 py-1.5 rounded-md">
              Changes Saved Successfully!
            </span>
          )}
          <button
            onClick={handleSaveChanges}
            disabled={saving}
            className="px-4 py-2 text-xs font-semibold text-white bg-[#238636] hover:bg-[#2ea043] disabled:bg-gray-700 rounded-md transition flex items-center gap-2"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-3.5 w-3.5 border-t-2 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
                Save Changes
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Panel layout */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        
        {/* Left Pane: PDF/HTML Preview */}
        <div className="w-full md:w-1/2 h-1/2 md:h-full border-r border-[#21262d] bg-[#0d1117] flex flex-col overflow-hidden">
          <div className="bg-[#161b22] px-4 py-2 border-b border-[#21262d] text-xs font-bold text-gray-400 flex items-center justify-between flex-shrink-0">
            <div className="flex space-x-4">
              <button 
                type="button"
                onClick={() => setLeftPaneTab('pdf')}
                className={`pb-1 border-b-2 transition ${leftPaneTab === 'pdf' ? 'border-[#58a6ff] text-white' : 'border-transparent hover:text-white'}`}
              >
                ORIGINAL PDF
              </button>
              <button 
                type="button"
                onClick={() => setLeftPaneTab('html')}
                className={`pb-1 border-b-2 transition ${leftPaneTab === 'html' ? 'border-[#58a6ff] text-white' : 'border-transparent hover:text-white'}`}
              >
                AI PORTFOLIO PREVIEW
              </button>
            </div>
            {leftPaneTab === 'pdf' ? (
              <a 
                href={`${API_URL}/resumes/${id}/pdf`} 
                target="_blank" 
                rel="noreferrer" 
                className="text-[#58a6ff] hover:underline"
              >
                Open PDF
              </a>
            ) : (
              <a 
                href={`${API_URL}/resumes/${id}/render`} 
                target="_blank" 
                rel="noreferrer" 
                className="text-[#58a6ff] hover:underline"
              >
                Open Site
              </a>
            )}
          </div>
          <div className="flex-1 bg-[#1e1e1e] relative">
            {leftPaneTab === 'pdf' ? (
              <iframe
                src={`${API_URL}/resumes/${id}/pdf`}
                className="w-full h-full border-0"
                title="Resume PDF Preview"
              />
            ) : (
              <iframe
                src={`${API_URL}/resumes/${id}/render`}
                className="w-full h-full border-0 bg-white"
                title="AI Rendered Portfolio"
              />
            )}
          </div>
        </div>

        {/* Right Pane: Form Editor */}
        <form onSubmit={handleSaveChanges} className="w-full md:w-1/2 h-1/2 md:h-full bg-[#0d1117] overflow-y-auto p-6 space-y-6">
          <div className="border-b border-[#21262d] pb-2">
            <h2 className="text-lg font-bold text-[#bc8cff]">CMS Schema Categories</h2>
            <p className="text-xs text-gray-400">Review the mapped metadata fields and headline-body pairs extracted by the AI layer.</p>
          </div>

          {/* Categorized Metadata */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 space-y-4">
            <h3 className="text-sm font-semibold text-[#58a6ff] border-b border-[#21262d] pb-2">Top-level Metadata</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Full Name</label>
                <input
                  type="text"
                  value={resumeData.content_json.name}
                  onChange={(e) => handleMetadataChange('name', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#58a6ff] transition"
                  placeholder="e.g. Samarth Rawat"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Email Address</label>
                <input
                  type="email"
                  value={resumeData.content_json.email}
                  onChange={(e) => handleMetadataChange('email', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#58a6ff] transition"
                  placeholder="e.g. email@example.com"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Phone Number</label>
                <input
                  type="text"
                  value={resumeData.content_json.number}
                  onChange={(e) => handleMetadataChange('number', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#58a6ff] transition"
                  placeholder="e.g. +91 12345 67890"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Postal Address</label>
                <input
                  type="text"
                  value={resumeData.content_json.address}
                  onChange={(e) => handleMetadataChange('address', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#58a6ff] transition"
                  placeholder="e.g. New Delhi, India"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-gray-400 mb-1.5 uppercase">Links & Portfolios (comma-separated)</label>
                <input
                  type="text"
                  value={resumeData.content_json.links}
                  onChange={(e) => handleMetadataChange('links', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#58a6ff] transition"
                  placeholder="e.g. github.com/user, linkedin.com/in/user"
                />
              </div>
            </div>
          </div>

          {/* Dynamic Headline-Body Sections */}
          {sectionsConfig.map((section) => (
            <div key={section.key} className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#21262d] pb-2 gap-2">
                <span className="text-sm font-semibold text-[#bc8cff] uppercase">{section.label}</span>
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] text-gray-500 font-bold uppercase">Headline:</span>
                  <input
                    type="text"
                    value={resumeData.content_json[section.key]?.headline || ''}
                    onChange={(e) => handleSectionChange(section.key, 'headline', e.target.value)}
                    className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-0.5 text-xs text-white focus:outline-none focus:border-[#bc8cff] transition w-full sm:w-60"
                    placeholder="Section Title"
                  />
                </div>
              </div>
              <div>
                <textarea
                  value={resumeData.content_json[section.key]?.body || ''}
                  onChange={(e) => handleSectionChange(section.key, 'body', e.target.value)}
                  rows={section.rows}
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#bc8cff] transition resize-y"
                  placeholder={`Write details of ${section.label}...`}
                />
              </div>
            </div>
          ))}

          {/* Save Button for Mobile views */}
          <div className="pt-4 flex justify-end md:hidden">
            <button
              type="submit"
              disabled={saving}
              className="w-full px-4 py-3 text-xs font-semibold text-white bg-[#238636] hover:bg-[#2ea043] disabled:bg-gray-700 rounded-md transition flex items-center justify-center gap-2"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
