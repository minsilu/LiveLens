import { useState, useEffect, useRef } from "react";
import { useParams, useLocation, Link } from "react-router";
import { venues as staticVenues } from "../data/venues.js";
import { ReviewCard } from "../components/ReviewCard.jsx";
import { ReviewFormModal } from "../components/ReviewFormModal.jsx";
import { Star, MapPin, ArrowLeft, ChevronDown, PenLine, Box, CheckCircle, Loader2 } from "lucide-react";
import { ImageWithFallback } from "../components/figma/ImageWithFallback";
import { Venue3DModal } from "../components/Venue3DModal.jsx";

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
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewsKey, setReviewsKey] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
  const successTimerRef = useRef(null);
  const [reviewOffset, setReviewOffset] = useState(0);
  const [reviewTotal, setReviewTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const PAGE_SIZE = 20;
  const [reviewSortId, setReviewSortId] = useState("most_recent");
  const [reviewSortOpen, setReviewSortOpen] = useState(false);
  const [sections, setSections] = useState([]);
  const [filterSection, setFilterSection] = useState("");
  const [sectionFilterOpen, setSectionFilterOpen] = useState(false);
  const [show3DModal, setShow3DModal] = useState(false);
  const reviewSortRef = useRef(null);
  const sectionFilterRef = useRef(null);

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
      if (sectionFilterRef.current && !sectionFilterRef.current.contains(e.target)) {
        setSectionFilterOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/search/seats?venue_id=${venueId}&limit=2000`)
      .then((r) => r.json())
      .then((data) => {
        const unique = [...new Set((data.results ?? []).map((s) => s.section))].sort();
        setSections(unique);
      })
      .catch(() => setSections([]));
  }, [venueId]);

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
    // Reset to first page whenever filters/sort/key change
    setReviewOffset(0);
    const params = new URLSearchParams({ venue_id: venueId, limit: PAGE_SIZE, offset: 0, sort_by: reviewSortBy, order: reviewOrder });
    if (filterSection) params.set("section", filterSection);
    fetch(`${API_BASE}/search/reviews?${params}`)
      .then((r) => r.json())
      .then((data) => { setReviews(data.results ?? []); setReviewTotal(data.total ?? 0); })
      .catch(() => setReviews([]));
  }, [venueId, reviewSortBy, reviewOrder, filterSection, reviewsKey]);

  function loadMoreReviews() {
    const nextOffset = reviewOffset + PAGE_SIZE;
    setLoadingMore(true);
    const params = new URLSearchParams({ venue_id: venueId, limit: PAGE_SIZE, offset: nextOffset, sort_by: reviewSortBy, order: reviewOrder });
    if (filterSection) params.set("section", filterSection);
    fetch(`${API_BASE}/search/reviews?${params}`)
      .then((r) => r.json())
      .then((data) => {
        setReviews((prev) => [...prev, ...(data.results ?? [])]);
        setReviewTotal(data.total ?? 0);
        setReviewOffset(nextOffset);
      })
      .catch(() => {})
      .finally(() => setLoadingMore(false));
  }

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
            <div className="absolute bottom-0 left-0 right-0 p-8 text-white flex justify-between items-end">
              <div>
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
              
              {/* 3D View Button at bottom right */}
              <button 
                onClick={() => setShow3DModal(true)}
                className="group flex items-center gap-3 px-5 py-3 bg-gray-900/60 hover:bg-black/70 backdrop-blur-md rounded-2xl border border-white/10 hover:border-blue-500/50 text-white font-medium transition-all duration-300 shadow-[0_8px_30px_rgba(0,0,0,0.5)] hover:shadow-[0_10px_40px_rgba(59,130,246,0.25)] hover:-translate-y-1"
              >
                <div className="bg-blue-500/20 p-2.5 rounded-xl group-hover:bg-blue-500/40 transition-colors border border-blue-500/20">
                  <Box className="w-5 h-5 text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                </div>
                <div className="flex flex-col items-start pr-1">
                  <span className="text-sm font-semibold tracking-wide text-gray-100 group-hover:text-white transition-colors">3D View</span>
                  <span className="text-[10px] text-blue-300/70 font-mono tracking-wider">INTERACTIVE</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/40 backdrop-blur-sm rounded-lg shadow-2xl p-8 border border-gray-700/50">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-white">Customer Reviews</h2>
              <p className="text-gray-400 mt-1">{reviews.length > 0 ? `${reviews.length} reviews shown` : "No reviews yet"}</p>
            </div>
            <div className="flex items-center gap-3">
            <div ref={sectionFilterRef} className="relative">
              <button
                onClick={() => setSectionFilterOpen(o => !o)}
                className="flex items-center justify-between gap-2 px-4 py-2 rounded-lg bg-gray-800/50 border border-gray-700 text-white hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 whitespace-nowrap w-36"
              >
                <span className="truncate">
                  Section: <span className="text-gray-300">{filterSection || "All"}</span>
                </span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${sectionFilterOpen ? "rotate-180" : ""}`} />
              </button>
              {sectionFilterOpen && (
                <div className="absolute right-0 mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-10 overflow-hidden max-h-56 overflow-y-auto">
                  <button
                    onClick={() => { setFilterSection(""); setSectionFilterOpen(false); }}
                    className={`w-full text-left px-4 py-3 text-sm transition-colors hover:bg-gray-700 ${!filterSection ? "text-blue-400 bg-gray-700/50" : "text-gray-200"}`}
                  >
                    All Sections
                  </button>
                  {sections.map((s) => (
                    <button
                      key={s}
                      onClick={() => { setFilterSection(s); setSectionFilterOpen(false); }}
                      className={`w-full text-left px-4 py-3 text-sm transition-colors hover:bg-gray-700 ${filterSection === s ? "text-blue-400 bg-gray-700/50" : "text-gray-200"}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div ref={reviewSortRef} className="relative">
              <button
                onClick={() => setReviewSortOpen(o => !o)}
                className="flex items-center justify-between gap-2 px-4 py-2 rounded-lg bg-gray-800/50 border border-gray-700 text-white hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 whitespace-nowrap w-60"
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
          </div>
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setShowReviewForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <PenLine className="w-4 h-4" />
              Write a Review
            </button>
          </div>

          {showReviewForm && (
            <ReviewFormModal
              venueId={venueId}
              onClose={() => {
                const y = window.scrollY;
                setShowReviewForm(false);
                requestAnimationFrame(() => window.scrollTo(0, y));
              }}
              onSuccess={() => {
                const y = window.scrollY;
                setShowReviewForm(false);
                setReviewsKey((k) => k + 1);
                requestAnimationFrame(() => window.scrollTo(0, y));
                // show success toast
                clearTimeout(successTimerRef.current);
                setShowSuccess(true);
                successTimerRef.current = setTimeout(() => setShowSuccess(false), 3000);
              }}
            />
          )}

          {/* Success toast */}
          <div
            style={{
              position: "fixed",
              bottom: "2rem",
              left: "50%",
              transform: showSuccess ? "translate(-50%, 0)" : "translate(-50%, 120%)",
              opacity: showSuccess ? 1 : 0,
              transition: "transform 0.35s cubic-bezier(0.34,1.56,0.64,1), opacity 0.3s ease",
              zIndex: 9999,
              pointerEvents: "none",
            }}
          >
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding: "0.875rem 1.5rem",
              background: "linear-gradient(135deg, #1a2e1a 0%, #0f2410 100%)",
              border: "1px solid rgba(74,222,128,0.35)",
              borderRadius: "1rem",
              boxShadow: "0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(74,222,128,0.1)",
              backdropFilter: "blur(12px)",
              minWidth: "280px",
            }}>
              <CheckCircle style={{ width: "1.25rem", height: "1.25rem", color: "#4ade80", flexShrink: 0 }} />
              <div>
                <p style={{ margin: 0, fontWeight: 600, color: "#f0fdf4", fontSize: "0.9rem" }}>Review posted!</p>
                <p style={{ margin: 0, color: "rgba(240,253,244,0.55)", fontSize: "0.75rem", marginTop: "0.1rem" }}>Thanks for sharing your experience.</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                review={{
                  id: review.id,
                  author: review.is_incognito
                    ? "Anonymous"
                    : (review.email ? review.email.split("@")[0] : "Verified Attendee"),
                  seatInfo: review.section && review.row ? `Section ${review.section}, Row ${review.row}${review.seat_number ? `, Seat ${review.seat_number}` : ""}` : null,
                  date: review.created_at ?? new Date().toISOString(),
                  rating: review.overall_rating,
                  ratingVisual: review.rating_visual,
                  ratingSound: review.rating_sound,
                  ratingValue: review.rating_value,
                  comment: review.text ?? "",
                  images: review.images ?? null,
                }}
              />
            ))}
          </div>

          {/* Load More */}
          {reviews.length < reviewTotal && (
            <div className="flex justify-center mt-6">
              <button
                onClick={loadMoreReviews}
                disabled={loadingMore}
                className="flex items-center gap-2 px-6 py-2.5 bg-gray-700/60 hover:bg-gray-700 disabled:opacity-50 border border-gray-600 hover:border-gray-500 text-gray-200 text-sm font-medium rounded-lg transition-all"
              >
                {loadingMore ? (
                  <><Loader2 className="w-4 h-4 animate-spin" />Loading...</>
                ) : (
                  `Load more (${reviewTotal - reviews.length} remaining)`
                )}
              </button>
            </div>
          )}
        </div>

        {/* 3D Modal */}
        {show3DModal && (
          <Venue3DModal 
            venueName={venue.name} 
            onClose={() => setShow3DModal(false)} 
          />
        )}
      </div>
    </div>
  );
}