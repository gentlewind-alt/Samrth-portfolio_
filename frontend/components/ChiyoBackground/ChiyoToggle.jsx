import React from 'react';

export default function ChiyoToggle({ enabled, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className={`fixed bottom-4 left-4 z-[10000] px-4 py-2 rounded-full font-bold shadow-lg transition-colors border ${
        enabled 
          ? 'bg-rose-500 text-white border-rose-600 hover:bg-rose-600' 
          : 'bg-white text-gray-800 border-gray-200 hover:bg-gray-100'
      }`}
      style={{
        fontFamily: 'sans-serif',
        backdropFilter: 'blur(4px)',
      }}
    >
      {enabled ? 'Chiyo Mode: ON' : 'Chiyo Mode: OFF'}
    </button>
  );
}
