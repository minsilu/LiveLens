import { useState, useEffect, useRef } from "react";
import { X, Star, Camera, ChevronDown } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function StarRating({ label, value, onChange }) {
  const [hovered, setHovered] = useState(0);
  const active = hovered || value;

  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-sm font-medium text-gray-300">{label}</span>
      <div className="flex gap-0.5" onMouseLeave={() => setHovered(0)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => onChange(star)}
            onMouseEnter={() => setHovered(star)}
            className="focus:outline-none"
          >
            <Star
              className={`w-6 h-6 transition-colors ${
                star <= active ? "fill-blue-500 text-blue-500" : "text-gray-600"
              }`}
            />
          </button>
        ))}
      </div>
      <span className="text-xs text-gray-500 h-4">{value > 0 ? `${value}/5` : ""}</span>
    </div>
  );
}

function EventCombobox({ events, value, onChange }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const selected = events.find((e) => e.event_id === value);
  const filtered = query.trim() === ""
    ? events
    : events.filter((e) => e.display_name.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <input
          type="text"
          value={open ? query : (selected?.display_name ?? "")}
          onChange={(e) => { setQuery(e.target.value); onChange(""); setOpen(true); }}
          onFocus={() => { setOpen(true); setQuery(""); }}
          placeholder="Search events..."
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
        />
        <ChevronDown className={`absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none transition-transform ${open ? "rotate-180" : ""}`} />
      </div>
      {open && (
        <div className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-56 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="px-4 py-3 text-sm text-gray-500">No events found</p>
          ) : (
            filtered.map((e) => (
              <button
                key={e.event_id}
                type="button"
                onClick={() => { onChange(e.event_id); setOpen(false); setQuery(""); }}
                className={`w-full text-left px-4 py-3 text-sm transition-colors hover:bg-gray-700 ${value === e.event_id ? "text-blue-400 bg-gray-700/50" : "text-gray-200"}`}
              >
                {e.display_name}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export function ReviewFormModal({ venueId, onClose }) {
  const [events, setEvents] = useState([]);
  const [seats, setSeats] = useState([]);
  const [eventId, setEventId] = useState("");
  const [section, setSection] = useState("");
  const [row, setRow] = useState("");
  const [seatNumber, setSeatNumber] = useState("");
  const [ratingVisual, setRatingVisual] = useState(0);
  const [ratingSound, setRatingSound] = useState(0);
  const [ratingValue, setRatingValue] = useState(0);
  const [reviewText, setReviewText] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);

  const numSort = (a, b) => (isNaN(a) || isNaN(b) ? a.localeCompare(b) : Number(a) - Number(b));
  const sections = [...new Set(seats.map((s) => s.section))].sort(numSort);
  const rows = [...new Set(seats.filter((s) => s.section === section).map((s) => s.row))].sort(numSort);
  const seatNumbers = [...new Set(seats.filter((s) => s.section === section && s.row === row).map((s) => s.seat_number))].sort(numSort);

  useEffect(() => {
    fetch(`${API_BASE}/review-form/events?venue_id=${venueId}`)
      .then((r) => r.json())
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setEvents([]));

    fetch(`${API_BASE}/search/seats?venue_id=${venueId}&limit=2000`)
      .then((r) => r.json())
      .then((data) => setSeats(data.results ?? []))
      .catch(() => setSeats([]));
  }, [venueId]);

  function handleSubmit(e) {
    e.preventDefault();
    // TODO: connect to POST /reviews/ with JWT token
  }

  return (
    <div className="mt-6 bg-gray-800/30 border border-gray-700 rounded-xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-700 px-6 py-4 bg-gray-800/50">
          <div>
            <h3 className="text-lg font-bold text-white">Write a Review</h3>
            <p className="text-xs text-gray-400 mt-0.5">Share your experience with the community</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-gray-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-8">

          {/* Event Selection */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Event Selection</h3>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Which event did you attend?</label>
              <EventCombobox events={events} value={eventId} onChange={setEventId} />
            </div>
          </section>

          {/* Seat Details */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Seat Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Section</label>
                <select
                  value={section}
                  onChange={(e) => { setSection(e.target.value); setRow(""); setSeatNumber(""); }}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
                >
                  <option value="">Select section...</option>
                  {sections.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Row</label>
                <select
                  value={row}
                  onChange={(e) => { setRow(e.target.value); setSeatNumber(""); }}
                  disabled={!section}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none disabled:opacity-40"
                >
                  <option value="">Select row...</option>
                  {rows.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Seat Number</label>
                <select
                  value={seatNumber}
                  onChange={(e) => setSeatNumber(e.target.value)}
                  disabled={!row}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none disabled:opacity-40"
                >
                  <option value="">Select seat...</option>
                  {seatNumbers.map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            </div>
          </section>

          {/* Ratings */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Your Ratings</h3>
            <div className="bg-gray-800/30 rounded-xl border border-gray-700 p-4 grid grid-cols-3 divide-x divide-gray-700">
              <StarRating label="Visual" value={ratingVisual} onChange={setRatingVisual} />
              <StarRating label="Sound" value={ratingSound} onChange={setRatingSound} />
              <StarRating label="Value" value={ratingValue} onChange={setRatingValue} />
            </div>
          </section>

          {/* Review Text */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Your Review</h3>
            <textarea
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              placeholder="Tell us about the view, acoustics, facilities..."
              rows={5}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-300 hover:bg-gray-700 transition-colors"
              >
                <Camera className="w-4 h-4" />
                Add Photos
              </button>
              <span className="text-xs text-gray-500">Max 5 images. High quality preferred.</span>
            </div>
          </section>

          {/* Footer */}
          <div className="pt-4 border-t border-gray-700 flex flex-col md:flex-row items-center justify-between gap-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-400">Post review anonymously</span>
            </label>
            <button
              type="submit"
              className="w-full md:w-auto px-10 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-lg shadow-blue-500/20 transition-all active:scale-95"
            >
              Post Review
            </button>
          </div>

        </form>
    </div>
  );
}
