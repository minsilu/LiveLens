import { createBrowserRouter } from "react-router";
import { LandingPage } from "./pages/LandingPage.jsx";
import { VenuePage } from "./pages/VenuePage.jsx";
import { LoginPage } from "./pages/LoginPage.jsx";
import { RegisterPage } from "./pages/RegisterPage.jsx";
import { ProfilePage } from "./pages/ProfilePage.jsx";
import { ReviewDetailPage } from "./pages/ReviewDetailPage.jsx";
import { NotFoundPage } from "./pages/NotFoundPage.jsx";
import { RootLayout } from "./components/RootLayout.jsx";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: LandingPage },
      { path: "venue/:venueId", Component: VenuePage },
      { path: "reviews/:reviewId", Component: ReviewDetailPage },
      { path: "login", Component: LoginPage },
      { path: "register", Component: RegisterPage },
      { path: "profile", Component: ProfilePage },
      { path: "*", Component: NotFoundPage },
    ],
  },
]);