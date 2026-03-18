import { useState } from "react";
import { Star, User } from "lucide-react";
import { ImageLightbox } from "./ImageLightbox";

export function ReviewCard({ review }) {
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const images = (() => {
    if (!review.images) return [];
    if (Array.isArray(review.images)) return review.images;
    try { return JSON.parse(review.images); } catch { return []; }
  })();
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="border border-gray-700 bg-gray-800/30 rounded-lg p-6 hover:border-gray-600 hover:bg-gray-800/50 transition-all">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
          <User className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="font-semibold text-white">{review.author}</h3>
              {review.seatInfo && (
                <p className="text-xs text-gray-500 mt-0.5">{review.seatInfo}</p>
              )}
            </div>
            <span className="text-sm text-gray-400">
              {formatDate(review.date)}
            </span>
          </div>
          <div className="flex items-center gap-1 mb-2">
            {[...Array(5)].map((_, index) => (
              <Star
                key={index}
                className={`w-4 h-4 ${
                  index < review.rating
                    ? "fill-yellow-400 text-yellow-400"
                    : "text-gray-600"
                }`}
              />
            ))}
          </div>
          {(review.ratingVisual || review.ratingSound || review.ratingValue) && (
            <div className="flex items-center gap-3 mb-3">
              {[
                { label: "Visual", value: review.ratingVisual },
                { label: "Sound", value: review.ratingSound },
                { label: "Value", value: review.ratingValue },
              ].map(({ label, value }) => value != null && (
                <span key={label} className="text-xs text-gray-500">
                  {label} <span className="text-gray-300">{value}/5</span>
                </span>
              ))}
            </div>
          )}
          <p className="text-gray-300 leading-relaxed">{review.comment}</p>
          {images.length > 0 && (
            <div className="flex gap-2 flex-wrap mt-3">
              {images.map((url, i) => (
                <img
                  key={i}
                  src={url}
                  onClick={() => setLightboxIndex(i)}
                  className="w-20 h-16 object-cover rounded-lg cursor-pointer border border-gray-700 hover:border-blue-500 transition-colors"
                />
              ))}
            </div>
          )}
          {lightboxIndex !== null && (
            <ImageLightbox
              images={images}
              startIndex={lightboxIndex}
              onClose={() => setLightboxIndex(null)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
