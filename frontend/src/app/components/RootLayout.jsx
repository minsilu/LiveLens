import { useState, useEffect } from "react";
import { Outlet, Link } from "react-router";
import { User, Sparkles } from "lucide-react";
import { GlobalChatPanel } from "./GlobalChatPanel.jsx";

export function RootLayout() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem("access_token"));

    function onStorage() {
      setIsLoggedIn(!!localStorage.getItem("access_token"));
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-900/95 backdrop-blur-md border-b border-gray-800 sticky top-0 z-50 shadow-lg shadow-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <img src="/icon.svg" alt="VenueHub" className="w-12 h-12" />
              <span className="text-xl font-bold text-white leading-none translate-y-0.5">VenueHub</span>
            </Link>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsChatOpen(true)}
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:text-white bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700/50 rounded-lg transition-colors"
              >
                <Sparkles className="w-4 h-4 text-blue-400" />
                <span className="hidden sm:block">Ask AI</span>
              </button>
              {isLoggedIn ? (
                <Link
                  to="/profile"
                  className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center hover:scale-105 transition-transform"
                >
                  <User className="w-5 h-5 text-white" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
                  >
                    Sign in
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    Sign up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <GlobalChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}

