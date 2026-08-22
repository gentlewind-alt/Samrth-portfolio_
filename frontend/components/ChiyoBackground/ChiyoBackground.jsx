import React, { useState, useEffect, useCallback, useRef } from 'react';
import ChiyoAnimation from './ChiyoAnimation';
import ChiyoToggle from './ChiyoToggle';

const CLICK_THRESHOLD = 300; // ms between clicks to count as rapid
const FAST_SLAP_THRESHOLD = 3; // number of clicks to trigger fast slap

export default function ChiyoBackground() {
  const [enabled, setEnabled] = useState(false);
  const [currentAnimation, setCurrentAnimation] = useState('idle');
  
  const clickCount = useRef(0);
  const lastClickTime = useRef(0);

  const handleGlobalClick = useCallback((e) => {
    if (!enabled) return;
    
    // Ignore clicks on the toggle button itself
    if (e.target.closest('.chiyo-toggle-container')) {
      return;
    }

    const now = Date.now();
    const timeSinceLastClick = now - lastClickTime.current;

    if (timeSinceLastClick < CLICK_THRESHOLD) {
      clickCount.current += 1;
    } else {
      clickCount.current = 1;
    }
    
    lastClickTime.current = now;

    if (clickCount.current >= FAST_SLAP_THRESHOLD) {
      setCurrentAnimation('fast_slap');
      clickCount.current = 0; // reset after triggering
    } else {
      if (currentAnimation !== 'fast_slap') {
        setCurrentAnimation('slap');
      }
    }
  }, [enabled, currentAnimation]);

  useEffect(() => {
    if (enabled) {
      window.addEventListener('click', handleGlobalClick);
      document.documentElement.classList.add('chiyo-active-override');
    } else {
      window.removeEventListener('click', handleGlobalClick);
      document.documentElement.classList.remove('chiyo-active-override');
      setCurrentAnimation('idle');
    }
    return () => {
      window.removeEventListener('click', handleGlobalClick);
      document.documentElement.classList.remove('chiyo-active-override');
    };
  }, [enabled, handleGlobalClick]);

  const handleAnimationComplete = useCallback((completedState) => {
    if (completedState === 'slap' || completedState === 'fast_slap') {
      setCurrentAnimation('idle');
    }
  }, []);

  const toggleChiyo = () => {
    setEnabled((prev) => !prev);
  };

  return (
    <>
      {enabled && (
        <style dangerouslySetInnerHTML={{ __html: `
          .chiyo-active-override body,
          .chiyo-active-override div[style*="background:#fafaf5"],
          .chiyo-active-override div[style*="background: #fafaf5"],
          .chiyo-active-override div[style*="background-color:#fafaf5"],
          .chiyo-active-override div[style*="background-color: #fafaf5"] {
            background: transparent !important;
            background-color: transparent !important;
          }
          .chiyo-active-override img[src*="vectorizer"] {
            display: none !important;
          }
        `}} />
      )}

      {/* Toggle button stays on top */}
      <div className="chiyo-toggle-container" style={{ position: 'fixed', bottom: '20px', left: '20px', zIndex: 9999 }}>
        <ChiyoToggle enabled={enabled} onToggle={toggleChiyo} />
      </div>

      {enabled && (
        <div style={{ position: 'fixed', inset: 0, zIndex: -1, pointerEvents: 'none' }}>
          {/* Layer 1 - Chiyo Animation */}
          <ChiyoAnimation 
            currentState={currentAnimation} 
            onAnimationComplete={handleAnimationComplete} 
          />
          {/* Layer 2 - Translucent Overlay */}
          <div 
            className="fixed inset-0"
            style={{ 
              backgroundColor: 'rgba(250, 250, 245, 0.75)', /* off-white tint */
              pointerEvents: 'none' 
            }} 
          />
        </div>
      )}
    </>
  );
}
