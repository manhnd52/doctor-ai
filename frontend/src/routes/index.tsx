import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Chatbot from "@/pages/ChatbotPage";
import Login from "@/pages/LoginPage";
import MainLayout from "@/layout/MainLayout";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("chat_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Chatbot />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}