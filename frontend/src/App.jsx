import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Listings from "./pages/Listings";
import ListingDetail from "./pages/ListingDetail";
import Contacts from "./pages/Contacts";
import Pipeline from "./pages/Pipeline";
import Documents from "./pages/Documents";
import Analytics from "./pages/Analytics";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="listings" element={<Listings />} />
            <Route path="listings/:id" element={<ListingDetail />} />
            <Route path="contacts" element={<Contacts />} />
            <Route path="pipeline" element={<Pipeline />} />
            <Route path="documents" element={<Documents />} />
            <Route path="analytics" element={<Analytics />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
