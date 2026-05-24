import React from 'react';

export async function getServerSideProps() {
  try {
    // 1. Fetch all resumes from backend to find the latest one
    const listRes = await fetch('http://127.0.0.1:8000/resumes/');
    if (!listRes.ok) throw new Error('Failed to fetch resumes list');
    const resumes = await listRes.json();

    if (resumes.length === 0) {
      // If no resumes exist, redirect to admin page to upload one
      return {
        redirect: {
          destination: '/admin',
          permanent: false,
        },
      };
    }

    // Sort by uploaded_at desc to find the latest
    resumes.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
    const latestResume = resumes[0];

    // 2. Fetch the rendered HTML of the latest resume
    const renderRes = await fetch(`http://127.0.0.1:8000/resumes/${latestResume.id}/render`);
    if (!renderRes.ok) throw new Error('Failed to fetch rendered resume');
    const html = await renderRes.text();

    return { props: { html } };
  } catch (err) {
    console.error('Error fetching resume:', err);
    return {
      props: {
        html: `
          <div style="min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0d1117; color: #c9d1d9; font-family: sans-serif; padding: 20px; text-align: center;">
            <h1 style="color: #f85149; margin-bottom: 10px;">Portfolio Offline</h1>
            <p style="margin-bottom: 20px;">Could not connect to the backend server. Make sure the FastAPI server is running on port 8000.</p>
            <a href="/admin" style="padding: 10px 20px; background: #238636; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; transition: background 0.2s;">Go to Admin Panel</a>
          </div>
        `
      }
    };
  }
}

export default function Home({ html }) {
  // Render the fetched portfolio HTML directly
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
