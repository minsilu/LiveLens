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
  MessageSquare,
  Send,
  Trash2,
} from "lucide-react";
import { ImageLightbox } from "../components/ImageLightbox";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/* ── Helper components ──────────────────────────────────────────────── */

function RatingBar({ label, value, icon: Icon, color, bgColor }) {
  const pct = ((value ?? 0) / 5) * 100;
  return (
    <div className="flex items-center gap-3">
      <div className={`flex items-center gap-1.5 w-24 shrink-0 ${color}`}>
        <Icon className="w-4 h-4" />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${bgColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm text-gray-400 w-8 text-right shrink-0">
        {value ?? "—"}/5
      </span>
    </div>
  );
}

function StarRow({ rating, size = "w-5 h-5" }) {
  return (
    <div className="flex items-center gap-1">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`${size} ${
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
    <div className="flex items-center gap-2 px-3 py-2.5 bg-gray-800/60 rounded-xl border border-gray-700/60">
      <Icon className={`w-4 h-4 shrink-0 ${colorClass}`} />
      <div>
        <p className="text-xs text-gray-500 leading-none mb-0.5">{label}</p>
        <p className={`text-sm font-medium leading-tight ${colorClass}`}>{value}</p>
      </div>
    </div>
  );
}

function SeatViewSkeleton() {
  return (
    <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-5 overflow-hidden">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-5 h-5 rounded bg-gray-700 animate-pulse" />
        <div className="h-4 w-40 rounded bg-gray-700 animate-pulse" />
      </div>
      <div className="relative w-full aspect-square rounded-xl bg-gray-700/50 overflow-hidden">
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

/* ── Main page component ────────────────────────────────────────────── */

export function ReviewDetailPage() {
  const { reviewId } = useParams();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lightboxIndex, setLightboxIndex] = useState(null);

  // Seat view image state — image_url + optional pin_x/pin_y
  const [seatViewData, setSeatViewData] = useState(null); // { image_url, pin_x, pin_y }
  const [seatViewLoading, setSeatViewLoading] = useState(false);

  // Sub-reviews state
  const [subReviews, setSubReviews] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  // Auth token from localStorage
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/reviews/${reviewId}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? "Review not found." : "Failed to load review.");
        return r.json();
      })
      .then((data) => {
        setReview(data);
        setSubReviews(data.sub_reviews ?? []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [reviewId]);

  // Fetch seat view image once review is loaded
  useEffect(() => {
    if (!review) return;
    const { venue_name, section, row, seat_number } = review;
    if (!venue_name || !section || !row || !seat_number) return;

    setSeatViewLoading(true);
    setSeatViewData(null);

    const params = new URLSearchParams({ venue_name, section, row, seat_number });
    fetch(`${API_BASE}/ai/seat-view-image?${params}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed");
        return r.json();
      })
      .then((data) => setSeatViewData(data))
      .catch(() => {})
      .finally(() => setSeatViewLoading(false));
  }, [review]);

  const handleSubmitComment = async () => {
    if (!newComment.trim() || !token) return;
    setSubmittingComment(true);
    try {
      const resp = await fetch(`${API_BASE}/reviews/${reviewId}/sub-reviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text: newComment.trim() }),
      });
      if (!resp.ok) throw new Error("Failed to post comment");
      setNewComment("");
      // Refetch sub-reviews
      const data = await fetch(`${API_BASE}/reviews/${reviewId}/sub-reviews`).then((r) => r.json());
      setSubReviews(data.sub_reviews ?? []);
    } catch {
      // silently fail for demo
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleDeleteComment = async (subReviewId) => {
    if (!token) return;
    try {
      const resp = await fetch(`${API_BASE}/reviews/${reviewId}/sub-reviews/${subReviewId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error("Failed");
      setSubReviews((prev) => prev.filter((sr) => sr.id !== subReviewId));
    } catch {
      // silently fail
    }
  };

  // Extract current user ID from JWT for ownership checks
  const currentUserId = (() => {
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.sub ?? null;
    } catch {
      return null;
    }
  })();

  const formatDate = (ds) => {
    if (!ds) return "—";
    return new Date(ds).toLocaleDateString("en-US", {
      year: "numeric", month: "long", day: "numeric",
    });
  };

  const formatDateShort = (ds) => {
    if (!ds) return "—";
    return new Date(ds).toLocaleDateString("en-US", {
      year: "numeric", month: "short", day: "numeric",
    });
  };

  const formatEventDate = (ds) => {
    if (!ds) return null;
    return new Date(ds).toLocaleDateString("en-US", {
      year: "numeric", month: "short", day: "numeric",
    });
  };

  // ── Loading / Error states ─────────────────────────────────────────
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

  const allLightboxImages = [...images];
  if (seatViewData?.image_url) {
    allLightboxImages.push({
      url:   seatViewData.image_url,
      pin_x: seatViewData.pin_x,
      pin_y: seatViewData.pin_y,
    });
  }

  const userEmailShort = (email) => {
    if (!email) return "Anonymous";
    const at = email.indexOf("@");
    if (at <= 2) return email;
    return email.substring(0, 2) + "***" + email.substring(at);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-7xl mx-auto px-6 py-10">

        {/* ── Back navigation ───────────────────────────────────────── */}
        <Link
          to={review.venue_id ? `/venue/${review.venue_id}` : "/"}
          className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          {review.venue_name ? `Back to ${review.venue_name}` : "Back to venues"}
        </Link>

        {/* ══════ TWO-COLUMN LAYOUT ══════ */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* ── LEFT COLUMN (2/5) ─────────────────────────────────── */}
          <div className="lg:col-span-2 space-y-6">

            {/* 2D Seat View */}
            {seatViewLoading && <SeatViewSkeleton />}
            {seatViewData?.image_url && !seatViewLoading && (
              <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-5 overflow-hidden">
                <div className="flex items-center gap-2 mb-3">
                  <Crosshair className="w-4 h-4 text-blue-400" />
                  <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                    Seat View — {seatLabel}
                  </h2>
                  <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/25 font-medium">
                    2D Map
                  </span>
                </div>
                {/* Seatmap image with CSS-positioned pin overlay */}
                <div
                  className="relative w-full cursor-pointer rounded-xl overflow-hidden border border-gray-700 hover:border-blue-500 transition-colors duration-200"
                  onClick={() => setLightboxIndex(images.length)}
                >
                  <img
                    src={seatViewData.image_url}
                    alt={`Seatmap for ${review.venue_name}`}
                    className="w-full block"
                  />
                  {seatViewData.pin_x != null && seatViewData.pin_y != null && (
                    <div
                      style={{
                        position: "absolute",
                        left: `${(seatViewData.pin_x / 1024) * 100}%`,
                        top:  `${(seatViewData.pin_y / 768)  * 100}%`,
                        transform: "translate(-50%, -50%)",
                        pointerEvents: "none",
                      }}
                    >
                      <div
                        style={{
                          width: "16px",
                          height: "16px",
                          borderRadius: "50%",
                          background: "rgba(220,38,38,0.92)",
                          border: "2px solid white",
                          boxShadow: "0 0 8px rgba(220,38,38,0.7)",
                          animation: "pulse-pin 2s ease-in-out infinite",
                        }}
                      />
                    </div>
                  )}
                </div>
                <style>{`
                  @keyframes pulse-pin {
                    0%, 100% { transform: scale(1);    }
                    50%      { transform: scale(1.08); }
                  }
                `}</style>
              </div>
            )}

            {/* User-uploaded Photos */}
            {images.length > 0 && (
              <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-5">
                <p className="text-xs text-gray-400 mb-3 font-semibold uppercase tracking-wide">
                  Photos ({images.length})
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {images.map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      onClick={() => setLightboxIndex(i)}
                      alt={`Review photo ${i + 1}`}
                      className="w-full aspect-square object-cover rounded-xl cursor-pointer border border-gray-700 hover:border-blue-500 hover:scale-[1.03] transition-all duration-200"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ── RIGHT COLUMN (3/5) ────────────────────────────────── */}
          <div className="lg:col-span-3 space-y-6">

            {/* Hero Review Card */}
            <div className="relative bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 overflow-hidden">
              <div className="h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />
              <div className="p-6">
                {/* Author row */}
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-white">Verified Attendee</p>
                    <p className="text-sm text-gray-500">{formatDate(review.created_at)}</p>
                  </div>
                  <div className="ml-auto text-right">
                    <StarRow rating={review.overall_rating} />
                    <p className="text-xs text-gray-500 mt-1">Overall {review.overall_rating}/5</p>
                  </div>
                </div>

                {/* Review text */}
                <p className="text-gray-200 leading-relaxed text-base whitespace-pre-line mb-5">
                  {review.text || <span className="italic text-gray-500">No comment provided.</span>}
                </p>

                {/* AI Tags */}
                {tags.length > 0 && (
                  <div className="flex items-start gap-2 flex-wrap">
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
              </div>
            </div>

            {/* Event Details */}
            <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-5">
              <p className="text-xs text-gray-400 mb-3 font-semibold uppercase tracking-wide">
                Event Details
              </p>
              <div className="grid grid-cols-2 gap-2">
                {review.venue_name && (
                  <Link
                    to={`/venue/${review.venue_id}`}
                    className="flex items-center gap-2 px-3 py-2.5 bg-gray-800/60 rounded-xl border border-gray-700/60 hover:border-blue-500/50 transition-colors group"
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
                <MetaBadge icon={Ticket} label="Event" value={review.event_name || null} colorClass="text-purple-300" />
                <MetaBadge icon={Calendar} label="Event Date" value={formatEventDate(review.event_date)} colorClass="text-gray-300" />
                <MetaBadge icon={MapPin} label="Seat" value={seatLabel} colorClass="text-gray-300" />
                {review.price_paid != null && (
                  <MetaBadge icon={DollarSign} label="Price Paid" value={`$${Number(review.price_paid).toFixed(2)}`} colorClass="text-green-400" />
                )}
              </div>
            </div>

            {/* Rating Breakdown */}
            <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
                Rating Breakdown
              </h2>
              <div className="space-y-3">
                <RatingBar label="Visual" value={review.rating_visual} icon={Eye} color="text-blue-400" bgColor="bg-blue-400" />
                <RatingBar label="Sound"  value={review.rating_sound}  icon={Volume2} color="text-purple-400" bgColor="bg-purple-400" />
                <RatingBar label="Value"  value={review.rating_value}  icon={BadgeDollarSign} color="text-pink-400" bgColor="bg-pink-400" />
              </div>
            </div>

            {/* Sub-Reviews / Comments */}
            <div className="bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 p-6">
              <div className="flex items-center gap-2 mb-5">
                <MessageSquare className="w-5 h-5 text-blue-400" />
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                  Comments ({subReviews.length})
                </h2>
              </div>

              {/* Comment list */}
              {subReviews.length > 0 ? (
                <div className="space-y-4 mb-6">
                  {subReviews.map((sr) => (
                    <div
                      key={sr.id}
                      className="flex gap-3 p-3 bg-gray-800/60 rounded-xl border border-gray-700/40 group/comment"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-300">
                            {userEmailShort(sr.user_email)}
                          </span>
                          <span className="text-xs text-gray-600">
                            {formatDateShort(sr.created_at)}
                          </span>
                          {currentUserId && sr.user_id === currentUserId && (
                            <button
                              onClick={() => handleDeleteComment(sr.id)}
                              title="Delete comment"
                              className="ml-auto p-1 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover/comment:opacity-100 transition-all"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                        <p className="text-sm text-gray-400 leading-relaxed">{sr.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-600 mb-6">No comments yet. Be the first to share your thoughts!</p>
              )}

              {/* Comment input */}
              {token ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Write a comment…"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSubmitComment()}
                    disabled={submittingComment}
                    className="flex-1 bg-gray-800/60 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:opacity-50"
                  />
                  <button
                    onClick={handleSubmitComment}
                    disabled={submittingComment || !newComment.trim()}
                    className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors flex items-center gap-2 text-sm font-medium"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="text-center py-3 bg-gray-800/40 rounded-xl border border-gray-700/40">
                  <p className="text-sm text-gray-500">
                    <Link to="/login" className="text-blue-400 hover:text-blue-300 transition-colors">Sign in</Link>
                    {" "}to leave a comment
                  </p>
                </div>
              )}
            </div>
          </div>

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
