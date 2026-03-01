import { createBrowserRouter } from "react-router";
import { LandingPage } from "./pages/LandingPage.jsx";
import { VenuePage } from "./pages/VenuePage.jsx";
import { RootLayout } from "./components/RootLayout.jsx";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: LandingPage },
      { path: "venue/:venueId", Component: VenuePage },
    ],
  },
]);