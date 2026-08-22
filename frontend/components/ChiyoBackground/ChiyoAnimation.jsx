import React, { useEffect, useRef } from 'react';

// Default configuration for the animation states
const ANIMATION_CONFIG = {
  idle: {
    folder: '/chiyo_idle',
    frames: 30, // adjust based on actual asset count
    fps: 12,
    loop: true
  },
  slap: {
    folder: '/chiyo_slap',
    frames: 29, 
    fps: 24,
    loop: false
  },
  fast_slap: {
    folder: '/chiyo_fast_slap',
    frames: 29,
    fps: 36, // faster playback
    loop: false
  }
};

export default function ChiyoAnimation({ currentState, onAnimationComplete }) {
  const canvasRef = useRef(null);
  const requestRef = useRef();
  const lastDrawTime = useRef(0);
  const frameRef = useRef(1);
  const imagesRef = useRef({});
  const currentAnimState = useRef(currentState);

  // Preload assets for the current state and IDLE (as it's the fallback)
  useEffect(() => {
    const preloadState = (stateName) => {
      if (!imagesRef.current[stateName]) {
        imagesRef.current[stateName] = [];
      }
      const config = ANIMATION_CONFIG[stateName];
      for (let i = 1; i <= config.frames; i++) {
        if (!imagesRef.current[stateName][i]) {
          const img = new Image();
          // Fallback to /chiyo/ if the specific folder doesn't exist yet for testing purposes, 
          // but attempt to load from the specific folder.
          img.src = `${config.folder}/frame${i}.png`;
          img.onerror = () => {
            // Fallback for current existing assets during development
            img.src = `/chiyo/frame${i}.png`;
          };
          imagesRef.current[stateName][i] = img;
        }
      }
    };

    preloadState('idle');
    preloadState('slap');
    preloadState('fast_slap');
  }, []);

  useEffect(() => {
    // When state changes, reset frame
    if (currentAnimState.current !== currentState) {
      frameRef.current = 1;
      currentAnimState.current = currentState;
    }
  }, [currentState]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const animate = (time) => {
      const config = ANIMATION_CONFIG[currentAnimState.current];
      const fpsInterval = 1000 / config.fps;

      if (time - lastDrawTime.current > fpsInterval) {
        lastDrawTime.current = time;

        const img = imagesRef.current[currentAnimState.current]?.[frameRef.current];
        
        if (img && img.complete && img.naturalWidth > 0) {
          // Clear canvas
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          
          // Draw image centered and scaled to fit or cover (adjust as needed for full screen)
          // Using object-fit cover logic for canvas
          const imgRatio = img.width / img.height;
          const canvasRatio = canvas.width / canvas.height;
          let drawWidth, drawHeight, offsetX, offsetY;

          if (canvasRatio > imgRatio) {
            drawWidth = canvas.width;
            drawHeight = canvas.width / imgRatio;
            offsetX = 0;
            offsetY = (canvas.height - drawHeight) / 2;
          } else {
            drawHeight = canvas.height;
            drawWidth = canvas.height * imgRatio;
            offsetX = (canvas.width - drawWidth) / 2;
            offsetY = 0;
          }

          ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
        }

        // Advance frame
        if (frameRef.current < config.frames) {
          frameRef.current++;
        } else {
          if (config.loop) {
            frameRef.current = 1;
          } else {
            // Animation finished
            if (onAnimationComplete) {
              onAnimationComplete(currentAnimState.current);
            }
          }
        }
      }
      
      requestRef.current = requestAnimationFrame(animate);
    };

    requestRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(requestRef.current);
    };
  }, [onAnimationComplete]);

  // Handle window resize to keep canvas full screen
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current) {
        canvasRef.current.width = window.innerWidth;
        canvasRef.current.height = window.innerHeight;
      }
    };
    
    handleResize(); // Init
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}
