import { Star, MapPin, Users, CalendarDays } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

function parseTags(tags) {
  try {
    const parsed = typeof tags === "string" ? JSON.parse(tags) : tags;
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function VenueCard({ venue }) {
  const tags = parseTags(venue.tags);
  const primaryTag = venue.category ?? (tags[0] ?? "Venue");
  const location = venue.address ?? venue.city ?? "—";
  const capacityStr = venue.capacity
    ? venue.capacity >= 1000
      ? (venue.capacity / 1000).toFixed(venue.capacity % 1000 === 0 ? 0 : 1) + "K"
      : venue.capacity.toLocaleString()
    : null;

  return (
    <div className="bg-gray-800/40 backdrop-blur-sm rounded-xl overflow-hidden border border-gray-700/50 hover:border-blue-500/40 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300 cursor-pointer group flex flex-col">
      {/* Image */}
      <div className="relative h-48 overflow-hidden shrink-0">
        <ImageWithFallback
          src={venue.image_url ?? venue.image ?? null}
          alt={venue.name}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent" />

        {/* Primary tag badge */}
        <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-md px-3 py-1 rounded-md border border-white/10">
          <span className="text-xs text-gray-200 font-medium capitalize">{primaryTag}</span>
        </div>

        {/* Upcoming events badge */}
        {venue.upcoming_events > 0 && (
          <div className="absolute bottom-3 left-3 flex items-center gap-1.5 bg-purple-600/80 backdrop-blur-md px-2.5 py-1 rounded-full border border-purple-400/30">
            <CalendarDays className="w-3 h-3 text-purple-200" />
            <span className="text-[11px] font-semibold text-purple-100">
              {venue.upcoming_events} upcoming
            </span>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-5 flex flex-col gap-2 flex-1">
        <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors leading-snug">
          {venue.name}
        </h3>

        {/* Rating row */}
        {venue.rating != null && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="font-semibold text-white text-sm">{venue.rating}</span>
            </div>
            {venue.reviewCount != null && (
              <span className="text-gray-400 text-xs">
                ({venue.reviewCount.toLocaleString()} reviews)
              </span>
            )}
          </div>
        )}

        {/* Location + capacity */}
        <div className="flex items-center justify-between text-gray-400 text-xs">
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{location}</span>
          </div>
          {capacityStr && (
            <div className="flex items-center gap-1 shrink-0 ml-2 bg-gray-700/60 px-2 py-0.5 rounded-full border border-gray-600/40">
              <Users className="w-3 h-3" />
              <span>{capacityStr}</span>
            </div>
          )}
        </div>

        {/* Tag pills — show up to 3 extra tags beyond the primary */}
        {tags.length > 1 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {tags.slice(1, 4).map((t) => (
              <span
                key={t}
                className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-gray-700/60 text-gray-400 border border-gray-600/40 capitalize"
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
