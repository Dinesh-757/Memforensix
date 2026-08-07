import React, { useState } from "react";
import { Box, Paper, TextField, Button, Typography, Alert, Stack, Link } from "@mui/material";
import SecurityIcon from "@mui/icons-material/Security";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/hooks/useAnalysis";
import { login } from "@/store/slices/authSlice";
import { authApi } from "@/services/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { loading, error } = useAppSelector((s) => s.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    try {
      if (isRegister) {
        await authApi.register(username, email, password, "analyst");
      }
      const result = await dispatch(login({ username, password }));
      if (login.fulfilled.match(result)) {
        navigate("/");
      }
    } catch (err: any) {
      setLocalError(err?.response?.data?.detail ?? "Something went wrong");
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "radial-gradient(circle at 50% 20%, #2b0000 0%, #0d0d0d 70%)",
      }}
    >
      <Paper sx={{ p: 4, width: 380 }}>
        <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
          <SecurityIcon sx={{ fontSize: 40, color: "#ff0000" }} />
          <Typography variant="h5" letterSpacing="0.1em">MEMFORENSIX</Typography>
          <Typography variant="caption" color="text.secondary">Digital Forensics Platform</Typography>
        </Stack>

        {(error || localError) && <Alert severity="error" sx={{ mb: 2 }}>{localError ?? error}</Alert>}

        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField
              label="Username" value={username} required
              onChange={(e) => setUsername(e.target.value)} fullWidth size="small"
            />
            {isRegister && (
              <TextField
                label="Email" type="email" value={email} required
                onChange={(e) => setEmail(e.target.value)} fullWidth size="small"
              />
            )}
            <TextField
              label="Password" type="password" value={password} required
              onChange={(e) => setPassword(e.target.value)} fullWidth size="small"
            />
            <Button type="submit" variant="contained" color="primary" disabled={loading} fullWidth>
              {isRegister ? "Register & Sign In" : "Sign In"}
            </Button>
          </Stack>
        </form>

        <Typography variant="body2" sx={{ mt: 2, textAlign: "center" }}>
          {isRegister ? "Already have an account? " : "Need an account? "}
          <Link component="button" onClick={() => setIsRegister(!isRegister)} underline="hover">
            {isRegister ? "Sign in" : "Register"}
          </Link>
        </Typography>
      </Paper>
    </Box>
  );
}
