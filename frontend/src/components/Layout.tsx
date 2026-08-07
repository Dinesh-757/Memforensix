import React from "react";
import {
  AppBar, Toolbar, Typography, Box, Drawer, List, ListItemButton,
  ListItemIcon, ListItemText, IconButton, Chip,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import SecurityIcon from "@mui/icons-material/Security";
import LogoutIcon from "@mui/icons-material/Logout";
import { useNavigate, useLocation } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/hooks/useAnalysis";
import { logout } from "@/store/slices/authSlice";

const DRAWER_WIDTH = 240;

const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Upload", path: "/upload", icon: <UploadFileIcon /> },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const username = useAppSelector((s) => s.auth.username);

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <SecurityIcon sx={{ mr: 1, color: "#ff0000" }} />
          <Typography variant="h6" noWrap sx={{ flexGrow: 1, letterSpacing: "0.1em" }}>
            MEMFORENSIX
          </Typography>
          <Chip label={username ?? "guest"} size="small" sx={{ mr: 2 }} />
          <IconButton color="inherit" onClick={() => { dispatch(logout()); navigate("/login"); }}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <List>
          {NAV_ITEMS.map((item) => (
            <ListItemButton
              key={item.path}
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                "&.Mui-selected": {
                  borderLeft: "3px solid #ff0000",
                  backgroundColor: "rgba(255,0,0,0.08)",
                },
              }}
            >
              <ListItemIcon sx={{ color: "#ff0000" }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, bgcolor: "background.default" }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
