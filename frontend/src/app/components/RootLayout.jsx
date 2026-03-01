import { Outlet } from "react-router";
import { Eye } from "lucide-react";

export function RootLayout() {
  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-900/95 backdrop-blur-md border-b border-gray-800 sticky top-0 z-50 shadow-lg shadow-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Eye className="w-8 h-8 text-blue-500" />
            <h1 className="text-2xl font-bold text-white">LiveLens</h1>
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
