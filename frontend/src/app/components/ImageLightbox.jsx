import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

export function ImageLightbox({ images, startIndex = 0, onClose }) {
  const [index, setIndex] = useState(startIndex);

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") setIndex((i) => (i + 1) % images.length);
      if (e.key === "ArrowLeft") setIndex((i) => (i - 1 + images.length) % images.length);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [images.length, onClose]);

  return createPortal(
    <div
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
      onClick={onClose}
    >
      <button
        onClick={onClose}
        className="absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-full bg-gray-800 hover:bg-gray-700 transition-colors"
      >
        <X className="w-5 h-5 text-white" />
      </button>

      {images.length > 1 && (
        <>
          <button
            onClick={(e) => { e.stopPropagation(); setIndex((i) => (i - 1 + images.length) % images.length); }}
            className="absolute left-4 w-10 h-10 flex items-center justify-center rounded-full bg-gray-800 hover:bg-gray-700 transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-white" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setIndex((i) => (i + 1) % images.length); }}
            className="absolute right-4 w-10 h-10 flex items-center justify-center rounded-full bg-gray-800 hover:bg-gray-700 transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-white" />
          </button>
        </>
      )}

      {/* Support plain URL strings and seatmap objects { url, pin_x, pin_y } */}
      {(() => {
        const item = images[index];
        const url  = typeof item === "string" ? item : item.url;
        const pinX = typeof item === "object" ? item.pin_x : null;
        const pinY = typeof item === "object" ? item.pin_y : null;

        return (
          <div
            className="relative flex items-center justify-center"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={url}
              className="max-h-[85vh] max-w-[90vw] object-contain rounded-lg block"
            />
            {pinX != null && pinY != null && (
              <div
                style={{
                  position: "absolute",
                  left: `${(pinX / 1024) * 100}%`,
                  top:  `${(pinY / 768)  * 100}%`,
                  transform: "translate(-50%, -50%)",
                  pointerEvents: "none",
                }}
              >
                <div style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  background: "rgba(220,38,38,0.92)",
                  border: "3px solid white",
                  boxShadow: "0 0 10px rgba(220,38,38,0.8)",
                  animation: "pulse-pin 2s ease-in-out infinite",
                }} />
              </div>
            )}
          </div>
        );
      })()}

      {images.length > 1 && (
        <div className="absolute bottom-4 flex gap-1.5">
          {images.map((_, i) => (
            <div key={i} className={`w-2 h-2 rounded-full transition-colors ${i === index ? "bg-white" : "bg-gray-600"}`} />
          ))}
        </div>
      )}

      <style>{`
        @keyframes pulse-pin {
          0%, 100% { transform: scale(1);    }
          50%      { transform: scale(1.08); }
        }
      `}</style>
    </div>,
    document.body
  );
}
