import { Star, User } from "lucide-react";

export function ReviewCard({ review }) {
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
            <h3 className="font-semibold text-white">{review.author}</h3>
            <span className="text-sm text-gray-400">
              {formatDate(review.date)}
            </span>
          </div>
          <div className="flex items-center gap-1 mb-3">
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
          <p className="text-gray-300 leading-relaxed">{review.comment}</p>
        </div>
      </div>
    </div>
  );
}
