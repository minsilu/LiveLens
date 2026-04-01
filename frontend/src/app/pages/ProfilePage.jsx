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
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
                <div key={review.id}>
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
                </div>
              ))}
            </div>
          )}
        </div>

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
