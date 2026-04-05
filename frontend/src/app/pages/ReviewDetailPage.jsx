import { useState, useEffect } from "react";
import { useParams, Link } from "react-router";
import {
  ArrowLeft,
  Star,
  MapPin,
  Calendar,
  Ticket,
  DollarSign,
  Eye,
  Volume2,
  BadgeDollarSign,
  User,
  Tag,
  Crosshair,
} from "lucide-react";
import { ImageLightbox } from "../components/ImageLightbox";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function RatingBar({ label, value, icon: Icon, color }) {
  const pct = ((value ?? 0) / 5) * 100;
  return (
    <div className="flex items-center gap-3">
      <div className={`flex items-center gap-1.5 w-24 shrink-0 ${color}`}>
        <Icon className="w-4 h-4" />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color.replace("text-", "bg-")}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm text-gray-400 w-8 text-right shrink-0">
        {value ?? "—"}/5
      </span>
    </div>
  );
}

function StarRow({ rating }) {
  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`w-5 h-5 ${
            i < rating ? "fill-yellow-400 text-yellow-400" : "text-gray-600"
          }`}
        />
      ))}
    </div>
  );
}

function MetaBadge({ icon: Icon, label, value, colorClass = "text-gray-300" }) {
  if (!value) return null;
  return (
    <div className="flex items-center gap-2 px-4 py-3 bg-gray-800/60 rounded-xl border border-gray-700/60">
      <Icon className={`w-4 h-4 shrink-0 ${colorClass}`} />
      <div>
        <p className="text-xs text-gray-500 leading-none mb-0.5">{label}</p>
        <p className={`text-sm font-medium ${colorClass}`}>{value}</p>
      </div>
    </div>
  );
}

function SeatViewSkeleton() {
  return (
    <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 mb-6 overflow-hidden">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-5 h-5 rounded bg-gray-700 animate-pulse" />
        <div className="h-4 w-48 rounded bg-gray-700 animate-pulse" />
      </div>
      <div className="relative w-full aspect-square rounded-xl bg-gray-700/50 overflow-hidden">
        {/* Shimmer overlay */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%)",
            animation: "shimmer 2s infinite",
          }}
        />
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-400 font-medium">Generating seat view…</p>
          <p className="text-xs text-gray-600">This may take a few seconds</p>
        </div>
      </div>
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}

export function ReviewDetailPage() {
  const { reviewId } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lightboxIndex, setLightboxIndex] = useState(null);

  // --- Seat view image state ---
  const [seatViewUrl, setSeatViewUrl] = useState(null);
  const [seatViewLoading, setSeatViewLoading] = useState(false);
  const [seatViewError, setSeatViewError] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/reviews/${reviewId}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? "Review not found." : "Failed to load review.");
        return r.json();
      })
      .then(setReview)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [reviewId]);

  // Fetch seat view image once review is loaded
  useEffect(() => {
    if (!review) return;
    const { venue_name, section, row, seat_number } = review;
    if (!venue_name || !section || !row || !seat_number) return;

    setSeatViewLoading(true);
    setSeatViewError(false);
    setSeatViewUrl(null);

    const params = new URLSearchParams({ venue_name, section, row, seat_number });
    fetch(`${API_BASE}/ai/seat-view-image?${params}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed");
        return r.json();
      })
      .then((data) => setSeatViewUrl(data.image_url))
      .catch(() => setSeatViewError(true))
      .finally(() => setSeatViewLoading(false));
  }, [review]);

  const formatDate = (ds) => {
    if (!ds) return "—";
    return new Date(ds).toLocaleDateString("en-US", {
      year: "numeric", month: "long", day: "numeric",
    });
  };

  const formatEventDate = (ds) => {
    if (!ds) return null;
    return new Date(ds).toLocaleDateString("en-US", {
      year: "numeric", month: "short", day: "numeric",
    });
  };

  // ── Loading state ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading review…</p>
        </div>
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center px-6">
        <div className="text-center">
          <Star className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-red-400 text-lg mb-6">{error}</p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to venues
          </Link>
        </div>
      </div>
    );
  }

  if (!review) return null;

  const images = Array.isArray(review.images) ? review.images : [];
  const tags   = Array.isArray(review.tags)   ? review.tags   : [];
  const seatLabel = [
    review.section && `Section ${review.section}`,
    review.row      && `Row ${review.row}`,
    review.seat_number && `Seat ${review.seat_number}`,
  ].filter(Boolean).join(", ") || null;

  // Build the combined image list for the lightbox (review images + seat view)
  const allLightboxImages = [...images];
  if (seatViewUrl) allLightboxImages.push(seatViewUrl);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-3xl mx-auto px-6 py-10">

        {/* ── Back navigation ───────────────────────────────────────────── */}
        <Link
          to={review.venue_id ? `/venue/${review.venue_id}` : "/"}
          className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          {review.venue_name ? `Back to ${review.venue_name}` : "Back to venues"}
        </Link>

        {/* ── Hero card ─────────────────────────────────────────────────── */}
        <div className="relative bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 overflow-hidden mb-6">
          {/* Decorative gradient band */}
          <div className="h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />

          <div className="p-8">
            {/* Author row */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                <User className="w-7 h-7 text-white" />
              </div>
              <div>
                <p className="font-semibold text-white text-lg">Verified Attendee</p>
                <p className="text-sm text-gray-500">{formatDate(review.created_at)}</p>
              </div>
              <div className="ml-auto">
                <StarRow rating={review.overall_rating} />
                <p className="text-right text-xs text-gray-500 mt-1">
                  Overall {review.overall_rating}/5
                </p>
              </div>
            </div>

            {/* Review text */}
            <p className="text-gray-200 leading-relaxed text-base whitespace-pre-line mb-6">
              {review.text || <span className="italic text-gray-500">No comment provided.</span>}
            </p>

            {/* AI Tags */}
            {tags.length > 0 && (
              <div className="flex items-start gap-2 flex-wrap mb-6">
                <Tag className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2.5 py-0.5 text-xs rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/25 font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Image gallery */}
            {images.length > 0 && (
              <div className="mb-2">
                <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                  Photos ({images.length})
                </p>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                  {images.map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      onClick={() => setLightboxIndex(i)}
                      alt={`Review photo ${i + 1}`}
                      className="w-full aspect-square object-cover rounded-xl cursor-pointer border border-gray-700 hover:border-blue-500 hover:scale-105 transition-all duration-200"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── AI-Generated Seat View ─────────────────────────────────────── */}
        {seatViewLoading && <SeatViewSkeleton />}
        {seatViewUrl && !seatViewLoading && (
          <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 mb-6 overflow-hidden">
            <div className="flex items-center gap-2 mb-4">
              <Crosshair className="w-5 h-5 text-blue-400" />
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                Seat View — {seatLabel}
              </h2>
              <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/25 font-medium">
                AI Generated
              </span>
            </div>
            <img
              src={seatViewUrl}
              alt={`2D seat map showing ${seatLabel} at ${review.venue_name}`}
              onClick={() => setLightboxIndex(images.length)}
              className="w-full rounded-xl cursor-pointer border border-gray-700 hover:border-blue-500 transition-colors duration-200"
            />
          </div>
        )}

        {/* ── Rating breakdown ──────────────────────────────────────────── */}
        <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6 mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
            Rating Breakdown
          </h2>
          <div className="space-y-3">
            <RatingBar
              label="Visual"
              value={review.rating_visual}
              icon={Eye}
              color="text-blue-400"
            />
            <RatingBar
              label="Sound"
              value={review.rating_sound}
              icon={Volume2}
              color="text-purple-400"
            />
            <RatingBar
              label="Value"
              value={review.rating_value}
              icon={BadgeDollarSign}
              color="text-pink-400"
            />
          </div>
        </div>

        {/* ── Metadata grid ─────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
          {review.venue_name && (
            <Link
              to={`/venue/${review.venue_id}`}
              className="flex items-center gap-2 px-4 py-3 bg-gray-800/60 rounded-xl border border-gray-700/60 hover:border-blue-500/50 transition-colors group"
            >
              <MapPin className="w-4 h-4 shrink-0 text-blue-400 group-hover:text-blue-300" />
              <div>
                <p className="text-xs text-gray-500 leading-none mb-0.5">Venue</p>
                <p className="text-sm font-medium text-blue-400 group-hover:text-blue-300 leading-tight">
                  {review.venue_name}
                </p>
              </div>
            </Link>
          )}
          <MetaBadge
            icon={Ticket}
            label="Event"
            value={review.event_name || null}
            colorClass="text-purple-300"
          />
          <MetaBadge
            icon={Calendar}
            label="Event Date"
            value={formatEventDate(review.event_date)}
            colorClass="text-gray-300"
          />
          <MetaBadge
            icon={MapPin}
            label="Seat"
            value={seatLabel}
            colorClass="text-gray-300"
          />
          {review.price_paid != null && (
            <MetaBadge
              icon={DollarSign}
              label="Price Paid"
              value={`$${Number(review.price_paid).toFixed(2)}`}
              colorClass="text-green-400"
            />
          )}
        </div>

      </div>

      {/* Lightbox */}
      {lightboxIndex !== null && (
        <ImageLightbox
          images={allLightboxImages}
          startIndex={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
        />
      )}
    </div>
  );
}

