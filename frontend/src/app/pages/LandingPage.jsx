import { useState, useEffect, useRef } from "react";
import { Link } from "react-router";
import { venues as staticVenues } from "../data/venues.js";
import { VenueCard } from "../components/VenueCard.jsx";
import { Search, Music, Users, Star, TrendingUp, ChevronDown } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function LandingPage() {
  const [query, setQuery] = useState("");
  const [venues, setVenues] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [featuredVenue, setFeaturedVenue] = useState(null);
  const [stats, setStats] = useState({
    totalVenues: 0,
    totalReviews: 0,
    avgRating: "0.0",
    satisfaction: 98
  });
  const [sortBy, setSortBy] = useState("name");
  const [order, setOrder] = useState("asc");
  // "name asc" = Relevance (default), "rating desc" = Rating
  const [sortOpen, setSortOpen] = useState(false);
  const sortRef = useRef(null);

  const sortOptions = [
    { label: "Relevance", sortBy: "name", order: "asc" },
    { label: "Rating", sortBy: "rating", order: "desc" },
  ];

  useEffect(() => {
    function handleClickOutside(e) {
      if (sortRef.current && !sortRef.current.contains(e.target)) {
        setSortOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/search/venues/stats`)
      .then((r) => r.json())
      .then((data) => {
        setStats({
          totalVenues: data.total_venues || 0,
          totalReviews: data.total_reviews || 0,
          avgRating: typeof data.avg_rating === 'number' ? data.avg_rating.toFixed(1) : "0.0",
          satisfaction: data.satisfaction || 98
        });
      })
      .catch((e) => console.error("Failed to fetch stats", e));
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      const params = new URLSearchParams({ limit: "50", sort_by: sortBy, order });
      if (query) params.set("q", query);
      setLoading(true);
      fetch(`${API_BASE}/search/venues?${params}`)
        .then((r) => r.json())
        .then((data) => {
          setVenues(data.results);
          setTotal(data.total);
          const scotiabank = data.results.find(v => v.name === "Scotiabank Arena" || v.name === "Scotiabank");
          if (scotiabank) setFeaturedVenue(scotiabank);
        })
        .catch(() => setVenues([]))
        .finally(() => setLoading(false));
    }, 150);
    return () => clearTimeout(timeout);
  }, [query, sortBy, order]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      {/* Hero Section with Stats */}
      <div className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
            backgroundSize: '40px 40px'
          }}></div>
        </div>
        
        {/* Featured Venue - Scotiabank Arena */}
        <div className="relative max-w-7xl mx-auto px-6 py-16">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left side - Text and Stats */}
            <div>
              <div className="inline-block px-4 py-2 bg-blue-500/20 rounded-full mb-6">
                <span className="text-blue-400 text-sm font-medium">Featured Venue</span>
              </div>
              <h1 className="text-5xl font-bold text-white mb-4">
                Scotiabank Arena
              </h1>
              <p className="text-xl text-gray-300 mb-8">
                Experience world-class performances at Toronto's premier entertainment destination
              </p>
              
              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-6 mb-8">
                <div className="text-center p-4 bg-white/5 rounded-lg backdrop-blur-sm border border-white/10">
                  <div className="text-3xl font-bold text-blue-400 mb-1">{featuredVenue ? featuredVenue.review_count : "-"}</div>
                  <div className="text-sm text-gray-400">Reviews</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg backdrop-blur-sm border border-white/10">
                  <div className="text-3xl font-bold text-purple-400 mb-1">{featuredVenue ? featuredVenue.rating : "-"}</div>
                  <div className="text-sm text-gray-400">Rating</div>
                </div>
                <div className="text-center p-4 bg-white/5 rounded-lg backdrop-blur-sm border border-white/10">
                  <div className="text-3xl font-bold text-pink-400 mb-1">{featuredVenue ? (featuredVenue.capacity >= 1000 ? (featuredVenue.capacity/1000).toFixed(1) + "K" : featuredVenue.capacity) : "-"}</div>
                  <div className="text-sm text-gray-400">Capacity</div>
                </div>
              </div>
              
              <Link 
                to={featuredVenue ? `/venue/${featuredVenue.id}` : "#"}
                className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                View Details
              </Link>
            </div>
            
            {/* Right side - Image */}
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-2xl blur-2xl"></div>
              <img 
                src={featuredVenue?.image_url || featuredVenue?.image || staticVenues[0].image}
                alt={featuredVenue ? featuredVenue.name : "Scotiabank Arena"}
                className="relative rounded-2xl shadow-2xl w-full h-[400px] object-cover border border-white/10"
              />
              <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-md px-4 py-2 rounded-lg border border-white/20">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  <span className="text-white font-semibold">{featuredVenue ? featuredVenue.rating : "-"}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Platform Stats */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
          <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 p-6 rounded-xl border border-blue-500/20">
            <Music className="w-10 h-10 text-blue-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1">{stats.totalVenues}</div>
            <div className="text-gray-400">Music Venues</div>
          </div>
          <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 p-6 rounded-xl border border-purple-500/20">
            <Users className="w-10 h-10 text-purple-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1">{stats.totalReviews.toLocaleString()}</div>
            <div className="text-gray-400">Total Reviews</div>
          </div>
          <div className="bg-gradient-to-br from-pink-500/10 to-pink-600/5 p-6 rounded-xl border border-pink-500/20">
            <Star className="w-10 h-10 text-pink-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1">{stats.avgRating}</div>
            <div className="text-gray-400">Average Rating</div>
          </div>
          <div className="bg-gradient-to-br from-green-500/10 to-green-600/5 p-6 rounded-xl border border-green-500/20">
            <TrendingUp className="w-10 h-10 text-green-400 mb-3" />
            <div className="text-3xl font-bold text-white mb-1">{stats.satisfaction}%</div>
            <div className="text-gray-400">Satisfaction</div>
          </div>
        </div>

        {/* Search and Venues */}
        <div className="mb-12 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Discover Music Venues
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Read authentic reviews from music lovers and find the perfect venue for your next live music experience
          </p>
        </div>

        <div className="mb-8 max-w-4xl mx-auto">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search venues..."
                className="w-full pl-12 pr-4 py-3 rounded-lg bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
              />
            </div>
            <div ref={sortRef} className="relative">
              <button
                onClick={() => setSortOpen(o => !o)}
                className="flex items-center justify-between gap-2 px-4 py-3 rounded-lg bg-gray-800/50 border border-gray-700 text-white hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 backdrop-blur-sm whitespace-nowrap w-48"
              >
                <span>Sort by: <span className="text-gray-300">{sortOptions.find(o => o.sortBy === sortBy && o.order === order)?.label ?? "Relevance"}</span></span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${sortOpen ? "rotate-180" : ""}`} />
              </button>
              {sortOpen && (
                <div className="absolute right-0 mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-10 overflow-hidden">
                  {sortOptions.map((opt) => (
                    <button
                      key={`${opt.sortBy}-${opt.order}`}
                      onClick={() => { setSortBy(opt.sortBy); setOrder(opt.order); setSortOpen(false); }}
                      className={`w-full text-left px-4 py-3 text-sm transition-colors hover:bg-gray-700 ${
                        sortBy === opt.sortBy && order === opt.order
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

        {loading && venues.length === 0 ? (
          <div className="text-center text-gray-400 py-12">Loading...</div>
        ) : venues.length === 0 ? (
          <div className="text-center text-gray-400 py-12">No venues found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {venues.map((venue, index) => (
              <Link key={venue.id} to={`/venue/${venue.id}`} state={{ venue, index }}>
                <VenueCard venue={{
                  ...venue,
                  image: staticVenues[index % staticVenues.length].image,
                  reviewCount: venue.review_count,
                }} />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}