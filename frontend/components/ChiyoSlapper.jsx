import React, { useState, useEffect, useCallback, useRef } from 'react';

export default function ChiyoSlapper() {
  const [slapCount, setSlapCount] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(1);
  const [isAnimating, setIsAnimating] = useState(false);
  const totalFrames = 29;
  const animationRef = useRef(null);
  
  // Preload images
  useEffect(() => {
    for (let i = 1; i <= totalFrames; i++) {
      const img = new Image();
      img.src = `/chiyo/frame${i}.png`;
    }
  }, []);

  // Fetch initial slap count
  useEffect(() => {
    const fetchSlaps = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/slaps');
        if (res.ok) {
          const data = await res.json();
          setSlapCount(data.count);
        }
      } catch (err) {
        console.error("Failed to fetch slaps", err);
      }
    };
    fetchSlaps();
    
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchSlaps, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSlap = async () => {
    // Optimistic update
    setSlapCount(prev => prev + 1);
    
    // Play animation
    if (!isAnimating) {
      setIsAnimating(true);
      let frame = 1;
      
      const animate = () => {
        frame++;
        if (frame <= totalFrames) {
          setCurrentFrame(frame);
          // 24 fps ~ 41ms per frame
          animationRef.current = setTimeout(animate, 40);
        } else {
          // Reset to first frame when done
          setCurrentFrame(1);
          setIsAnimating(false);
        }
      };
      
      animate();
    }

    // Update backend
    try {
      await fetch('http://localhost:8000/api/slaps', {
        method: 'POST'
      });
    } catch (err) {
      console.error("Failed to post slap", err);
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) clearTimeout(animationRef.current);
    };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-white rounded-2xl shadow-2xl my-2 relative overflow-hidden border border-gray-200" style={{ minWidth: '220px', zIndex: 9999 }}>
      <h2 className="text-sm font-bold mb-1 font-serif text-gray-800 drop-shadow-sm">Global Slaps</h2>
      
      <div className="text-3xl font-black mb-3 text-rose-500 drop-shadow-md">
        {slapCount.toLocaleString()}
      </div>

      <div 
        onClick={handleSlap}
        className="cursor-pointer transition-transform hover:scale-105 active:scale-95 select-none relative"
      >
        <img 
          src={`/chiyo/frame${currentFrame}.png`} 
          alt="Chiyo being slapped" 
          className="rounded-xl pointer-events-none w-full object-contain"
          style={{ width: '180px', height: '140px' }}
        />
        <div className="absolute inset-0 rounded-xl hover:bg-black hover:bg-opacity-5 transition-colors"></div>
      </div>
      
      <p className="mt-3 text-gray-400 font-mono text-[10px] tracking-wide font-bold">
        CLICK TO SLAP
      </p>
    </div>
  );
}
