import React from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { Provider } from "react-redux";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { store } from "@/store";
import { theme } from "@/theme";
import { useAppSelector } from "@/hooks/useAnalysis";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import UploadPage from "@/pages/UploadPage";
import AnalysisView from "@/pages/AnalysisView";
import LoginPage from "@/pages/LoginPage";

function RequireAuth({ children }: { children: React.ReactElement }) {
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout><Dashboard /></Layout>
          </RequireAuth>
        }
      />
      <Route
        path="/upload"
        element={
          <RequireAuth>
            <Layout><UploadPage /></Layout>
          </RequireAuth>
        }
      />
      <Route
        path="/analysis/:id"
        element={
          <RequireAuth>
            <Layout><AnalysisView /></Layout>
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  );
}
