import { X, Box, Rotate3D, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

export function Venue3DModal({ venueName, onClose }) {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Disable body scroll when modal mounts
    document.body.style.overflow = 'hidden';
    
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1500);
    
    return () => {
      // Re-enable scroll when unmounts
      document.body.style.overflow = 'auto';
      clearTimeout(timer);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal Container */}
      <div 
        className="relative w-full max-w-5xl h-[80vh] bg-gray-900 rounded-2xl border border-gray-700 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col transform transition-all animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/80 backdrop-blur-md relative z-20">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-xl border border-blue-500/30">
              <Rotate3D className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold flex items-center gap-2">
                3D Venue View
                <span className="px-2 py-0.5 rounded text-[10px] uppercase tracking-wider bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30">
                  Concept
                </span>
              </h2>
              <p className="text-gray-400 text-sm truncate max-w-xs">{venueName}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-xl text-gray-400 hover:text-white transition-all hover:scale-105 active:scale-95"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 3D Viewport Placeholder */}
        <div className="flex-1 relative bg-[#0a0a0a] flex items-center justify-center overflow-hidden">
          {/* Decorative Grid Background */}
          <div 
            className="absolute inset-0 z-0 opacity-20"
            style={{
              backgroundImage: `linear-gradient(to right, #374151 1px, transparent 1px), linear-gradient(to bottom, #374151 1px, transparent 1px)`,
              backgroundSize: '40px 40px',
              backgroundPosition: 'center center'
            }}
          />
          
          {/* Glowing Center */}
          <div 
            className="absolute inset-0 z-0" 
            style={{
              background: 'radial-gradient(circle at center, rgba(59,130,246,0.15) 0%, transparent 60%)'
            }}
          />

          {loading ? (
            <div className="relative z-10 flex flex-col items-center gap-6">
              <div className="relative">
                <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full animate-pulse" />
                <Loader2 className="w-12 h-12 text-blue-400 animate-spin relative z-10 drop-shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
              </div>
              <p className="text-sm font-medium tracking-[0.2em] text-blue-400 animate-pulse">
                INITIALIZING 3D ENGINE
              </p>
            </div>
          ) : (
            <div className="relative z-10 flex flex-col items-center text-center max-w-md p-10 bg-gray-900/40 backdrop-blur-xl rounded-3xl border border-gray-700/50 shadow-[0_0_40px_rgba(0,0,0,0.4)] animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out">
              <div className="p-4 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl border border-gray-600/30 mb-6 shadow-inner">
                <Box className="w-16 h-16 text-blue-400 drop-shadow-[0_0_15px_rgba(59,130,246,0.6)] animate-bounce" style={{ animationDuration: '3s' }} />
              </div>
              
              <h3 className="text-2xl font-bold font-sans text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 mb-3">
                Interactive 3D View
              </h3>
              
              <p className="text-gray-400 text-sm mb-8 leading-relaxed">
                This area is ready to integrate a WebGL or WebXR-based 3D venue renderer (e.g., using Three.js, React Three Fiber, or a commercial provider like Seats.io).
              </p>
              
              <div className="flex gap-4 w-full">
                <button 
                  onClick={(e) => {
                     const btn = e.currentTarget;
                     btn.textContent = "Not Connected";
                     setTimeout(() => btn.textContent = "Explore Seats", 2000);
                  }}
                  className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg hover:shadow-blue-500/25 border border-white/10"
                >
                  Explore Seats
                </button>
                <button 
                  onClick={(e) => {
                     const btn = e.currentTarget;
                     btn.textContent = "Coming Soon";
                     setTimeout(() => btn.textContent = "Section View", 2000);
                  }}
                  className="flex-1 py-3 bg-gray-800 hover:bg-gray-700 text-white border border-gray-600 rounded-xl text-sm font-semibold transition-all shadow-lg hover:shadow-xl"
                >
                  Section View
                </button>
              </div>
            </div>
          )}

          {/* HUD Overlay mock elements */}
          {!loading && (
            <>
              <div className="absolute top-6 right-6 flex flex-col gap-3 z-10 animate-in fade-in duration-1000 delay-300">
                <button className="w-10 h-10 bg-gray-800/80 hover:bg-gray-700 backdrop-blur-md border border-gray-700 hover:border-gray-500 rounded-xl flex items-center justify-center transition-all text-gray-300 hover:text-white group">
                  <div className="relative">
                    <div className="w-4 h-[2px] bg-current rounded-full" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[2px] h-4 bg-current rounded-full" />
                  </div>
                </button>
                <button className="w-10 h-10 bg-gray-800/80 hover:bg-gray-700 backdrop-blur-md border border-gray-700 hover:border-gray-500 rounded-xl flex items-center justify-center transition-all text-gray-300 hover:text-white">
                  <div className="w-4 h-[2px] bg-current rounded-full" />
                </button>
              </div>
              <div className="absolute bottom-6 left-6 z-10 animate-in fade-in duration-1000 delay-500">
                <div className="bg-gray-900/80 backdrop-blur-md px-4 py-2 rounded-lg border border-gray-700/50 flex flex-col gap-1">
                  <p className="text-[10px] font-mono text-green-400 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    FPS: 60
                  </p>
                  <p className="text-[10px] font-mono text-blue-400 uppercase opacity-80">
                    Engine: WebGL2 Placeholder
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
