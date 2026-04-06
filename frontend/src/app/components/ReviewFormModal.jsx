import { useState, useEffect, useRef } from "react";
import { Link } from "react-router";
import { X, Star, Camera, ChevronDown, Loader2, CheckCircle, LogIn, AlertCircle } from "lucide-react";
import { createPortal } from "react-dom";
import { ImageLightbox } from "./ImageLightbox";

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

export function ReviewFormModal({ venueId, onClose, onSuccess }) {
  const [events, setEvents] = useState([]);
  const [seats, setSeats] = useState([]);
  const [eventId, setEventId] = useState("");
  const [section, setSection] = useState("");
  const [row, setRow] = useState("");
  const [seatNumber, setSeatNumber] = useState("");
  const [ratingVisual, setRatingVisual] = useState(0);
  const [ratingSound, setRatingSound] = useState(0);
  const [ratingValue, setRatingValue] = useState(0);
  const [pricePaid, setPricePaid] = useState("");
  const [reviewText, setReviewText] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState([]);
  const [draftId, setDraftId] = useState(null);
  const [savingDraft, setSavingDraft] = useState(false);
  const [draftSaved, setDraftSaved] = useState(false);
  const fileInputRef = useRef(null);

  const isLoggedIn = !!localStorage.getItem("access_token");

  useEffect(() => {
    fetch(`${API_BASE}/review-form/events?venue_id=${venueId}`)
      .then((r) => r.json())
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setEvents([]));
  }, [venueId]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const token = localStorage.getItem("access_token");
    fetch(`${API_BASE}/review-drafts/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(drafts => {
        if (!Array.isArray(drafts)) return;
        const venueDraft = drafts.find(d => d.draft_data?.venue_id === venueId);
        if (venueDraft) {
          setDraftId(venueDraft.id);
          const data = venueDraft.draft_data;
          if (data.event_id) setEventId(data.event_id);
          if (data.section) setSection(data.section);
          if (data.row) setRow(data.row);
          if (data.seat_number) setSeatNumber(data.seat_number);
          if (data.rating_visual) setRatingVisual(data.rating_visual);
          if (data.rating_sound) setRatingSound(data.rating_sound);
          if (data.rating_value) setRatingValue(data.rating_value);
          if (data.price_paid) setPricePaid(data.price_paid);
          if (data.text) setReviewText(data.text);
          if (data.is_anonymous !== undefined) setIsAnonymous(data.is_anonymous);
        }
      })
      .catch(console.error);
  }, [venueId, isLoggedIn]);

  function handleFileChange(e) {
    const files = Array.from(e.target.files);
    const remaining = 5 - selectedFiles.length;
    const toAdd = files.slice(0, remaining).map((file) => ({
      file,
      preview: URL.createObjectURL(file),
    }));
    setSelectedFiles((prev) => [...prev, ...toAdd]);
    e.target.value = "";
  }

  function removeFile(index) {
    setSelectedFiles((prev) => {
      URL.revokeObjectURL(prev[index].preview);
      return prev.filter((_, i) => i !== index);
    });
  }

  async function handleSaveDraft() {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    setSavingDraft(true);

    const draftData = {
      venue_id: venueId,
      event_id: eventId,
      section,
      row,
      seat_number: seatNumber,
      rating_visual: ratingVisual,
      rating_sound: ratingSound,
      rating_value: ratingValue,
      price_paid: pricePaid,
      text: reviewText,
      is_anonymous: isAnonymous
    };

    try {
      const res = await fetch(`${API_BASE}/review-drafts/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ id: draftId, draft_data: draftData })
      });
      if (res.ok) {
        const data = await res.json();
        setDraftId(data.draft_id);
        setDraftSaved(true);
        setTimeout(() => setDraftSaved(false), 2000);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSavingDraft(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem("access_token");
    if (!token) return;

    // Validation
    const errs = [];
    if (!eventId) errs.push("Please select an event.");
    if (!section || !row || !seatNumber) errs.push("Please select your seat (section, row, and seat number).");
    if (!ratingVisual || !ratingSound || !ratingValue) errs.push("Please rate all three categories (Visual, Sound, Value).");
    if (!reviewText.trim()) errs.push("Please write your review.");
    if (errs.length > 0) {
      setErrors(errs);
      return;
    }
    setErrors([]);

    setSubmitting(true);
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

    const res = await fetch(`${API_BASE}/reviews/`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        event_id: eventId,
        venue_id: venueId,
        section,
        row,
        seat_number: seatNumber,
        rating_visual: ratingVisual,
        rating_sound: ratingSound,
        rating_value: ratingValue,
        price_paid: pricePaid ? parseFloat(pricePaid) : 0,
        text: reviewText,
      }),
    });
    if (!res.ok) {
      setSubmitting(false);
      return alert("Failed to submit review.");
    }
    const { review_id } = await res.json();

    if (selectedFiles.length > 0) {
      const imageUrls = [];
      for (let i = 0; i < selectedFiles.length; i++) {
        const { file } = selectedFiles[i];
        const formData = new FormData();
        formData.append("file", file);
        const params = new URLSearchParams({ review_id, pic_num: i + 1 });
        const uploadRes = await fetch(`${API_BASE}/reviews/upload-image?${params}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
        if (!uploadRes.ok) continue;
        const { url } = await uploadRes.json();
        imageUrls.push(url);
      }

      if (imageUrls.length > 0) {
        await fetch(`${API_BASE}/reviews/img-database?review_id=${review_id}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify({ images: imageUrls }),
        });
      }
    }

    if (draftId) {
      await fetch(`${API_BASE}/review-drafts/delete?draft_id=${draftId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
    }

    setSubmitting(false);
    setSubmitted(true);
    setTimeout(() => (onSuccess ?? onClose)(), 2000);
  }

  // Not logged in — show login prompt instead of form
  if (!isLoggedIn) {
    return createPortal(
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
        <div className="w-full max-w-md bg-gray-900 border border-gray-700 rounded-xl shadow-2xl">
          <div className="flex flex-col items-center justify-center gap-4 py-12 px-8 text-center">
            <div className="w-14 h-14 rounded-full bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              <LogIn className="w-7 h-7 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Sign in to write a review</h3>
              <p className="text-gray-400 text-sm mt-1">Share your experience with the community</p>
            </div>
            <div className="flex gap-3">
              <Link to="/login" className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
                Sign in
              </Link>
              <button onClick={onClose} className="px-6 py-2.5 bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium rounded-lg transition-colors">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>,
      document.body
    );
  }

  if (submitted) {
    return createPortal(
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
        <div className="w-full max-w-md bg-gray-900 border border-green-500/30 rounded-xl shadow-2xl">
          <div className="flex flex-col items-center justify-center gap-4 py-16 px-8 text-center">
            <div className="w-16 h-16 rounded-full bg-green-500/15 border border-green-500/30 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Review Posted!</h3>
              <p className="text-gray-400 text-sm mt-1">Thanks for sharing your experience with the community.</p>
            </div>
          </div>
        </div>
      </div>,
      document.body
    );
  }

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-gray-900 border border-gray-700 rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-700 px-6 py-4 bg-gray-800/50 sticky top-0 z-10 backdrop-blur-sm shrink-0">
          <div>
            <h3 className="text-lg font-bold text-white">Write a Review</h3>
            <p className="text-xs text-gray-400 mt-0.5">Share your experience</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleSaveDraft}
              disabled={savingDraft || submitting}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium rounded-lg transition-all flex items-center gap-1"
            >
              {savingDraft ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
              {draftSaved ? "Saved!" : "Save Draft"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium rounded-lg transition-all"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-70 text-white text-sm font-bold rounded-lg shadow-lg shadow-blue-500/20 transition-all flex items-center gap-1"
            >
              {submitting ? (
                <><Loader2 className="w-3 h-3 animate-spin" />Posting...</>
              ) : "Post"}
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto w-full" style={{scrollbarWidth: 'thin'}}>

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
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Section</label>
                <input
                  type="text"
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  placeholder="e.g. 101"
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Row</label>
                <input
                  type="text"
                  value={row}
                  onChange={(e) => setRow(e.target.value)}
                  placeholder="e.g. A"
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Seat No</label>
                <input
                  type="text"
                  value={seatNumber}
                  onChange={(e) => setSeatNumber(e.target.value)}
                  placeholder="e.g. 1"
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </section>

          {/* Price Paid */}
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Price Paid (optional)</h3>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">$</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={pricePaid}
                onChange={(e) => setPricePaid(e.target.value)}
                placeholder="0.00"
                className="w-full bg-gray-800 border border-gray-600 rounded-lg pl-8 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
              />
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
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleFileChange}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={selectedFiles.length >= 5}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-300 hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Camera className="w-4 h-4" />
                Add Photos
              </button>
              <span className="text-xs text-gray-500">
                {selectedFiles.length}/5 images selected.
              </span>
            </div>
            {selectedFiles.length > 0 && (
              <div className="flex gap-2 flex-wrap mt-2">
                {selectedFiles.map((f, i) => (
                  <div key={i} className="relative group">
                    <img
                      src={f.preview}
                      onClick={() => setLightboxIndex(i)}
                      className="w-20 h-16 object-cover rounded-lg cursor-pointer border border-gray-600 hover:border-blue-500 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => removeFile(i)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-gray-900 border border-gray-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3 text-gray-300" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {lightboxIndex !== null && (
              <ImageLightbox
                images={selectedFiles.map((f) => f.preview)}
                startIndex={lightboxIndex}
                onClose={() => setLightboxIndex(null)}
              />
            )}
          </section>

          {/* Validation Errors */}
          {errors.length > 0 && (
            <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 space-y-1">
              {errors.map((err, i) => (
                <p key={i} className="text-red-400 text-sm flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  {err}
                </p>
              ))}
            </div>
          )}

          <div className="pt-2 border-t border-gray-700 mt-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-400">Post review anonymously</span>
            </label>
          </div>

        </form>
      </div>
    </div>,
    document.body
  );
}
