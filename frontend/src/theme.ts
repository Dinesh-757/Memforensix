import { createTheme } from "@mui/material/styles";

// MEMFORENSIX red & black theme
export const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#ff0000", contrastText: "#ffffff" },
    secondary: { main: "#8b0000" },
    background: {
      default: "#0d0d0d",
      paper: "#1a0a0a",
    },
    error: { main: "#ff1744" },
    warning: { main: "#ff9100" },
    success: { main: "#00e676" },
    text: {
      primary: "#f5f5f5",
      secondary: "#bdbdbd",
    },
    divider: "rgba(255, 0, 0, 0.15)",
  },
  typography: {
    fontFamily: '"JetBrains Mono", "Roboto Mono", "Consolas", monospace',
    h1: { fontWeight: 700, letterSpacing: "0.05em" },
    h2: { fontWeight: 700, letterSpacing: "0.03em" },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 6 },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "#1a0a0a",
          backgroundImage: "linear-gradient(90deg, #1a0a0a 0%, #2b0000 100%)",
          borderBottom: "1px solid #8b0000",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: "1px solid rgba(139,0,0,0.35)",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none", fontWeight: 600 },
        containedPrimary: {
          background: "linear-gradient(135deg, #8b0000 0%, #ff0000 100%)",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { backgroundColor: "#0d0d0d", borderRight: "1px solid #8b0000" },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600 },
      },
    },
  },
});

export const severityColor: Record<string, string> = {
  critical: "#ff1744",
  high: "#ff5722",
  medium: "#ff9100",
  low: "#ffc107",
};
