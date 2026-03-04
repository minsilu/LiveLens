import { Outlet, Link } from "react-router";
import ChatWindow from "./Chat/ChatWindow";

export function RootLayout() {
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
            </div>
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <ChatWindow />
    </div>
  );
}
