import { useParams, Link } from "react-router";
import { venues } from "../data/venues.js";
import { ReviewCard } from "../components/ReviewCard.jsx";
import { Star, MapPin, ArrowLeft } from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";

export function VenuePage() {
  const { venueId } = useParams();
  const venue = venues.find((v) => v.id === venueId);

  if (!venue) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <p className="text-center text-gray-400">Venue not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to venues
        </Link>

        <div className="bg-gray-800/40 backdrop-blur-sm rounded-lg shadow-2xl overflow-hidden mb-8 border border-gray-700/50">
          <div className="relative h-96 overflow-hidden">
            <ImageWithFallback
              src={venue.image}
              alt={venue.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
              <div className="mb-2">
                <span className="bg-blue-500/30 backdrop-blur-sm px-3 py-1 rounded-full text-sm border border-blue-400/30">
                  {venue.category}
                </span>
              </div>
              <h1 className="text-4xl font-bold mb-3">{venue.name}</h1>
              <div className="flex items-center gap-4 mb-3">
                <div className="flex items-center gap-2">
                  <Star className="w-6 h-6 fill-yellow-400 text-yellow-400" />
                  <span className="text-2xl font-semibold">{venue.rating}</span>
                  <span className="text-white/80">
                    ({venue.reviewCount} reviews)
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 text-white/90">
                <MapPin className="w-5 h-5" />
                <span>{venue.address}</span>
              </div>
            </div>
          </div>

          <div className="p-8">
            <h2 className="text-2xl font-semibold text-white mb-3">
              About
            </h2>
            <p className="text-gray-300 text-lg leading-relaxed">
              {venue.description}
            </p>
          </div>
        </div>

        <div className="bg-gray-800/40 backdrop-blur-sm rounded-lg shadow-2xl p-8 border border-gray-700/50">
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-white">
              Customer Reviews
            </h2>
            <p className="text-gray-400 mt-1">
              {venue.reviewCount} total reviews
            </p>
          </div>

          <div className="space-y-4">
            {venue.reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}