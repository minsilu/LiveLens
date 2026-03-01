import { Star, MapPin } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

export function VenueCard({ venue }) {
  return (
    <div className="bg-gray-800/40 backdrop-blur-sm rounded-lg overflow-hidden border border-gray-700/50 hover:border-gray-600 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300 cursor-pointer group">
      <div className="relative h-48 overflow-hidden">
        <ImageWithFallback
          src={venue.image}
          alt={venue.name}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent" />
        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md px-3 py-1 rounded-md border border-white/10">
          <span className="text-sm text-gray-200">{venue.category}</span>
        </div>
      </div>
      <div className="p-5">
        <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
          {venue.name}
        </h3>
        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center gap-1">
            <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
            <span className="font-semibold text-white">{venue.rating}</span>
          </div>
          <span className="text-gray-400 text-sm">
            ({venue.reviewCount.toLocaleString()} reviews)
          </span>
        </div>
        <div className="flex items-start gap-2 text-gray-400">
          <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span className="text-sm">{venue.address}</span>
        </div>
      </div>
    </div>
  );
}
