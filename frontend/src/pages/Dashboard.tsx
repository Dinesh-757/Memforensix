import React, { useEffect } from "react";
import {
  Box, Typography, Grid, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, LinearProgress, Stack,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/hooks/useAnalysis";
import { fetchAnalyses } from "@/store/slices/analysisSlice";
import { formatBytes, formatDate, statusColor, truncate } from "@/utils/helpers";

function StatCard({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <Paper sx={{ p: 2, textAlign: "center", borderColor: accent }}>
      <Typography variant="h4" sx={{ color: accent ?? "#ff0000", fontWeight: 700 }}>
        {value}
      </Typography>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
    </Paper>
  );
}

export default function Dashboard() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, total, loading } = useAppSelector((s) => s.analysis);

  useEffect(() => {
    dispatch(fetchAnalyses());
    const interval = setInterval(() => dispatch(fetchAnalyses()), 8000);
    return () => clearInterval(interval);
  }, [dispatch]);

  const running = items.filter((a) => a.status === "running" || a.status === "queued").length;
  const completed = items.filter((a) => a.status === "completed").length;
  const failed = items.filter((a) => a.status === "failed").length;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4">Dashboard</Typography>
        <Button variant="contained" startIcon={<UploadFileIcon />} onClick={() => navigate("/upload")}>
          New Analysis
        </Button>
      </Stack>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}><StatCard label="Total Analyses" value={total} /></Grid>
        <Grid item xs={6} md={3}><StatCard label="In Progress" value={running} accent="#ff9100" /></Grid>
        <Grid item xs={6} md={3}><StatCard label="Completed" value={completed} accent="#00e676" /></Grid>
        <Grid item xs={6} md={3}><StatCard label="Failed" value={failed} accent="#ff1744" /></Grid>
      </Grid>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Filename</TableCell>
              <TableCell>Format</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Created</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Typography color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
                    No analyses yet. Upload a memory dump to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {items.map((a) => (
              <TableRow key={a.id} hover sx={{ cursor: "pointer" }} onClick={() => navigate(`/analysis/${a.id}`)}>
                <TableCell sx={{ fontFamily: "monospace" }}>{truncate(a.filename, 40)}</TableCell>
                <TableCell>{a.dump_format.toUpperCase()}</TableCell>
                <TableCell>{formatBytes(a.file_size)}</TableCell>
                <TableCell><Chip label={a.status} size="small" color={statusColor(a.status)} /></TableCell>
                <TableCell sx={{ width: 140 }}>
                  <LinearProgress variant="determinate" value={a.progress} sx={{ height: 6, borderRadius: 3 }} />
                </TableCell>
                <TableCell>{formatDate(a.created_at)}</TableCell>
                <TableCell>
                  <Button size="small" onClick={(e) => { e.stopPropagation(); navigate(`/analysis/${a.id}`); }}>
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
