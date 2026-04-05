import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router";
import { ReviewCard } from "../components/ReviewCard.jsx";
import {
  User,
  Mail,
  Calendar,
  Clock,
  Star,
  MessageSquare,
  MapPin,
  LogOut,
  Shield,
  ChevronRight,
  Trash2,
  AlertTriangle,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      navigate("/login");
      return;
    }

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (r.status === 401) {
          localStorage.removeItem("access_token");
          navigate("/login");
          return null;
        }
        if (!r.ok) throw new Error("Failed to load profile");
        return r.json();
      })
      .then((data) => {
        if (data) setProfile(data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [navigate]);

  function handleLogout() {
    localStorage.removeItem("access_token");
    window.dispatchEvent(new Event("storage"));
    navigate("/");
  }

  async function handleDeleteReview(reviewId) {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API_BASE}/reviews/${reviewId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Failed to delete review");
      }
      // Remove from local state instantly
      setProfile((prev) => ({
        ...prev,
        reviews: prev.reviews.filter((r) => r.id !== reviewId),
        stats: {
          ...prev.stats,
          total_reviews: Math.max(0, prev.stats.total_reviews - 1),
        },
      }));
    } catch (err) {
      alert(err.message);
    } finally {
      setDeleting(false);
      setConfirmDeleteId(null);
    }
  }

  function formatDate(dateString) {
    if (!dateString) return "—";
    const d = new Date(dateString);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function getInitials(email) {
    if (!email) return "?";
    return email.charAt(0).toUpperCase();
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-400">Loading your profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <Link
            to="/"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Go home
          </Link>
        </div>
      </div>
    );
  }

  if (!profile) return null;

  const { user, stats, reviews } = profile;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* ── Profile Hero ── */}
        <div className="relative bg-gray-800/40 backdrop-blur-sm rounded-2xl border border-gray-700/50 overflow-hidden mb-8">
          {/* Decorative gradient band */}
          <div className="h-32 bg-gradient-to-r from-blue-600/30 via-purple-600/30 to-pink-600/30" />

          <div className="px-8 pb-8 -mt-14 flex flex-col sm:flex-row items-start sm:items-end gap-6">
            {/* Avatar */}
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-4xl font-bold text-white shadow-xl border-4 border-gray-800 flex-shrink-0">
              {getInitials(user.email)}
            </div>

            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-white truncate">
                {user.email}
              </h1>
              <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-400">
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4" />
                  Member since {formatDate(user.created_at)}
                </span>
                {user.last_login && (
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4" />
                    Last login {formatDate(user.last_login)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Stats Cards ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-10">
          <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 p-6 rounded-xl border border-blue-500/20">
            <MessageSquare className="w-9 h-9 text-blue-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1">
              {stats.total_reviews}
            </div>
            <div className="text-gray-400 text-sm">Total Reviews</div>
          </div>

          <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 p-6 rounded-xl border border-yellow-500/20">
            <Star className="w-9 h-9 text-yellow-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1">
              {stats.avg_rating > 0 ? stats.avg_rating : "—"}
            </div>
            <div className="text-gray-400 text-sm">Average Rating</div>
          </div>

          <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 p-6 rounded-xl border border-purple-500/20">
            <MapPin className="w-9 h-9 text-purple-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1 truncate">
              {stats.top_venue ?? "—"}
            </div>
            <div className="text-gray-400 text-sm">Top Venue</div>
          </div>
        </div>

        {/* ── Account Settings ── */}
        <div className="bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6 mb-10">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-gray-400" />
            Account Settings
          </h2>
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-white text-sm font-medium">Email</p>
                <p className="text-gray-500 text-xs">{user.email}</p>
              </div>
            </div>
          </div>
        </div>

        {/* ── My Reviews ── */}
        <div className="bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-gray-400" />
            My Reviews
            {reviews.length > 0 && (
              <span className="text-sm text-gray-500 font-normal">
                ({reviews.length})
              </span>
            )}
          </h2>

          {reviews.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 mb-2">
                You haven't written any reviews yet.
              </p>
              <Link
                to="/"
                className="text-blue-400 hover:text-blue-300 text-sm font-medium inline-flex items-center gap-1"
              >
                Explore venues
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {reviews.map((review) => (
                <div key={review.id} className="relative group/card">
                  {/* Venue badge above the review card */}
                  <Link
                    to={`/venue/${review.venue_id}`}
                    className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 mb-2 transition-colors"
                  >
                    <MapPin className="w-3 h-3" />
                    {review.venue_name}
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                  <ReviewCard
                    review={{
                      id: review.id,
                      author: user.is_incognito
                        ? "Anonymous"
                        : user.email,
                      seatInfo:
                        review.section && review.row
                          ? `Section ${review.section}, Row ${review.row}${
                              review.seat_number
                                ? `, Seat ${review.seat_number}`
                                : ""
                            }`
                          : null,
                      date:
                        review.created_at ?? new Date().toISOString(),
                      rating: review.overall_rating,
                      ratingVisual: review.rating_visual,
                      ratingSound: review.rating_sound,
                      ratingValue: review.rating_value,
                      comment: review.text ?? "",
                      images: review.images ?? null,
                    }}
                  />
                  {/* Delete button — appears on hover */}
                  <button
                    onClick={() => setConfirmDeleteId(review.id)}
                    title="Delete this review"
                    className="absolute top-3 right-3 p-1.5 rounded-lg bg-gray-900/80 text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 opacity-0 group-hover/card:opacity-100 transition-all duration-200 z-10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Delete Confirmation Dialog (page-centered overlay) ── */}
        {confirmDeleteId && (
          <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div className="bg-gray-800 border border-gray-700 rounded-2xl p-6 max-w-sm w-full shadow-2xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-xl bg-red-500/10 text-red-400">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <h3 className="text-white font-semibold text-lg">Delete Review?</h3>
              </div>
              <p className="text-gray-400 text-sm mb-6">
                This action is permanent and cannot be undone. All comments on this review will also be removed.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmDeleteId(null)}
                  disabled={deleting}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteReview(confirmDeleteId)}
                  disabled={deleting}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {deleting ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  {deleting ? "Deleting…" : "Delete"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Log Out ── */}
        <div className="mt-10 flex justify-center">
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-6 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl border border-red-500/20 transition-colors text-sm font-medium"
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
        </div>
      </div>
    </div>
  );
}
