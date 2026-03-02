import { useState, useEffect, useRef } from "react";
import { useParams, useLocation, Link } from "react-router";
import { venues as staticVenues } from "../data/venues.js";
import { ReviewCard } from "../components/ReviewCard.jsx";
import { Star, MapPin, ArrowLeft, ChevronDown } from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function parseFirstTag(tags) {
  try {
    const parsed = typeof tags === "string" ? JSON.parse(tags) : tags;
    return Array.isArray(parsed) && parsed.length > 0 ? parsed[0] : "Venue";
  } catch {
    return "Venue";
  }
}

export function VenuePage() {
  const { venueId } = useParams();
  const location = useLocation();
  const [venue, setVenue] = useState(location.state?.venue ?? null);
  const [venueIndex, setVenueIndex] = useState(location.state?.index ?? 0);
  const [loading, setLoading] = useState(!venue);
  const [reviews, setReviews] = useState([]);
  const [reviewSortId, setReviewSortId] = useState("relevance");
  const [reviewSortOpen, setReviewSortOpen] = useState(false);
  const reviewSortRef = useRef(null);

  const reviewSortOptions = [
    { id: "relevance",     label: "Relevance",     sortBy: "overall_rating", order: "desc" },
    { id: "highest",       label: "Highest Rated", sortBy: "overall_rating", order: "desc" },
    { id: "lowest",        label: "Lowest Rated",  sortBy: "overall_rating", order: "asc" },
    { id: "most_recent",   label: "Most Recent",   sortBy: "created_at",     order: "desc" },
  ];

  const activeSort = reviewSortOptions.find(o => o.id === reviewSortId) ?? reviewSortOptions[0];
  const reviewSortBy = activeSort.sortBy;
  const reviewOrder = activeSort.order;

  useEffect(() => {
    function handleClickOutside(e) {
      if (reviewSortRef.current && !reviewSortRef.current.contains(e.target)) {
        setReviewSortOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (venue) return;
    fetch(`${API_BASE}/search/venues?limit=100`)
      .then((r) => r.json())
      .then((data) => {
        const idx = data.results.findIndex((v) => v.id === venueId);
        if (idx !== -1) {
          setVenue(data.results[idx]);
          setVenueIndex(idx);
        }
      })
      .finally(() => setLoading(false));
  }, [venueId]);

  useEffect(() => {
    fetch(`${API_BASE}/search/reviews?venue_id=${venueId}&limit=20&sort_by=${reviewSortBy}&order=${reviewOrder}`)
      .then((r) => r.json())
      .then((data) => setReviews(data.results ?? []))
      .catch(() => setReviews([]));
  }, [venueId, reviewSortBy, reviewOrder]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <p className="text-center text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!venue) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <p className="text-center text-gray-400">Venue not found</p>
        </div>
      </div>
    );
  }

  const image = venue.image ?? staticVenues[venueIndex % staticVenues.length].image;
  const category = venue.category ?? parseFirstTag(venue.tags);
  const location_str = venue.address ?? venue.city ?? "—";

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
              src={image}
              alt={venue.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
              <div className="mb-2">
                <span className="bg-blue-500/30 backdrop-blur-sm px-3 py-1 rounded-full text-sm border border-blue-400/30">
                  {category}
                </span>
              </div>
              <h1 className="text-4xl font-bold mb-3">{venue.name}</h1>
              {venue.rating != null && (
                <div className="flex items-center gap-2 mb-3">
                  <Star className="w-6 h-6 fill-yellow-400 text-yellow-400" />
                  <span className="text-2xl font-semibold">{venue.rating}</span>
                  {(venue.review_count ?? venue.reviewCount) != null && (
                    <span className="text-white/80">({(venue.review_count ?? venue.reviewCount).toLocaleString()} reviews)</span>
                  )}
                </div>
              )}
              <div className="flex items-center gap-2 text-white/90">
                <MapPin className="w-5 h-5" />
                <span>{location_str}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/40 backdrop-blur-sm rounded-lg shadow-2xl p-8 border border-gray-700/50">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-white">Customer Reviews</h2>
              <p className="text-gray-400 mt-1">{reviews.length > 0 ? `${reviews.length} reviews shown` : "No reviews yet"}</p>
            </div>
            <div ref={reviewSortRef} className="relative">
              <button
                onClick={() => setReviewSortOpen(o => !o)}
                className="flex items-center justify-between gap-2 px-4 py-2 rounded-lg bg-gray-800/50 border border-gray-700 text-white hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 whitespace-nowrap w-64"
              >
                <span className="truncate">Sort by: <span className="text-gray-300">{activeSort.label}</span></span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${reviewSortOpen ? "rotate-180" : ""}`} />
              </button>
              {reviewSortOpen && (
                <div className="absolute right-0 mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-10 overflow-hidden">
                  {reviewSortOptions.map((opt) => (
                    <button
                      key={`${opt.sortBy}-${opt.order}`}
                      onClick={() => { setReviewSortId(opt.id); setReviewSortOpen(false); }}
                      className={`w-full text-left px-4 py-3 text-sm transition-colors hover:bg-gray-700 ${
                        reviewSortId === opt.id
                          ? "text-blue-400 bg-gray-700/50"
                          : "text-gray-200"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="space-y-4">
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                review={{
                  author: "Verified Attendee",
                  seatInfo: review.section && review.row ? `Section ${review.section}, Row ${review.row}` : null,
                  date: review.created_at ?? new Date().toISOString(),
                  rating: review.overall_rating,
                  comment: review.text ?? "",
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}