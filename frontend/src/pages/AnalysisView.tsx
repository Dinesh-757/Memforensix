import React, { useEffect, useState } from "react";
import {
  Box, Typography, Tabs, Tab, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, Button, Stack, Grid, CircularProgress,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector, useAnalysisProgress } from "@/hooks/useAnalysis";
import { fetchAnalysisResults, clearCurrentResults } from "@/store/slices/analysisSlice";
import { analysisApi } from "@/services/api";
import ProcessTree from "@/components/ProcessTree";
import NetworkGraph from "@/components/NetworkGraph";
import Timeline from "@/components/Timeline";
import ThreatIndicators from "@/components/ThreatIndicators";
import ProgressTracker from "@/components/ProgressTracker";
import { statusColor } from "@/utils/helpers";

export default function AnalysisView() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useAppDispatch();
  const { currentResults } = useAppSelector((s) => s.analysis);
  const [tab, setTab] = useState(0);
  const liveProgress = useAnalysisProgress(id);

  useEffect(() => {
    if (!id) return;
    dispatch(fetchAnalysisResults(id));
    return () => { dispatch(clearCurrentResults()); };
  }, [id, dispatch]);

  useEffect(() => {
    if (liveProgress?.stage === "complete" && id) {
      dispatch(fetchAnalysisResults(id));
    }
  }, [liveProgress?.stage, id, dispatch]);

  if (!currentResults) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 8 }}>
        <CircularProgress color="error" />
      </Box>
    );
  }

  const { analysis, processes, connections, yara_matches, ml_findings, summary } = currentResults;
  const isRunning = analysis.status === "running" || analysis.status === "queued";

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
        <Box>
          <Typography variant="h4">{analysis.filename}</Typography>
          <Typography variant="body2" color="text.secondary" fontFamily="monospace">
            SHA-256: {analysis.file_hash_sha256}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip label={analysis.status} color={statusColor(analysis.status)} />
          {analysis.status === "completed" && (
            <>
              <Button size="small" startIcon={<DownloadIcon />} onClick={() => analysisApi.downloadExport(analysis.id, "pdf")}>PDF</Button>
              <Button size="small" startIcon={<DownloadIcon />} onClick={() => analysisApi.downloadExport(analysis.id, "json")}>JSON</Button>
              <Button size="small" startIcon={<DownloadIcon />} onClick={() => analysisApi.downloadExport(analysis.id, "csv")}>CSV</Button>
            </>
          )}
        </Stack>
      </Stack>

      {isRunning && (
        <Box sx={{ mb: 3 }}>
          <ProgressTracker
            status={liveProgress ? "running" : analysis.status}
            progress={liveProgress?.progress ?? analysis.progress}
            stage={liveProgress?.stage}
            message={liveProgress?.message}
          />
        </Box>
      )}

      {analysis.status === "failed" && (
        <Paper sx={{ p: 2, mb: 3, borderColor: "#ff1744" }}>
          <Typography color="error">Analysis failed: {analysis.error_message}</Typography>
        </Paper>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(summary).map(([k, v]) => (
          <Grid item xs={6} md={3} key={k}>
            <Paper sx={{ p: 1.5, textAlign: "center" }}>
              <Typography variant="h5" color="#ff0000">{v}</Typography>
              <Typography variant="caption" color="text.secondary">{k.replace(/_/g, " ")}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} textColor="inherit" TabIndicatorProps={{ style: { backgroundColor: "#ff0000" } }} sx={{ mb: 2 }}>
        <Tab label="Processes" />
        <Tab label="Process Tree" />
        <Tab label="Network" />
        <Tab label="Timeline" />
        <Tab label="Threats" />
      </Tabs>

      {tab === 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>PID</TableCell><TableCell>PPID</TableCell><TableCell>Name</TableCell>
                <TableCell>Threads</TableCell><TableCell>Handles</TableCell><TableCell>Cmdline</TableCell>
                <TableCell>Flag</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {processes.map((p) => (
                <TableRow key={p.pid} sx={p.is_suspicious ? { backgroundColor: "rgba(255,23,68,0.08)" } : {}}>
                  <TableCell>{p.pid}</TableCell>
                  <TableCell>{p.ppid ?? "—"}</TableCell>
                  <TableCell sx={{ fontFamily: "monospace" }}>{p.name}</TableCell>
                  <TableCell>{p.threads}</TableCell>
                  <TableCell>{p.handles}</TableCell>
                  <TableCell sx={{ fontFamily: "monospace", fontSize: 12 }}>{p.cmdline}</TableCell>
                  <TableCell>{p.is_suspicious && <Chip label="suspicious" color="error" size="small" />}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {tab === 1 && <ProcessTree processes={processes} />}

      {tab === 2 && (
        <>
          <NetworkGraph connections={connections} />
          <TableContainer component={Paper} sx={{ mt: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Process</TableCell><TableCell>Local</TableCell><TableCell>Remote</TableCell>
                  <TableCell>Protocol</TableCell><TableCell>State</TableCell><TableCell>Flag</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {connections.map((c, i) => (
                  <TableRow key={i} sx={c.is_suspicious ? { backgroundColor: "rgba(255,23,68,0.08)" } : {}}>
                    <TableCell>{c.process_name}</TableCell>
                    <TableCell sx={{ fontFamily: "monospace" }}>{c.local_addr}:{c.local_port}</TableCell>
                    <TableCell sx={{ fontFamily: "monospace" }}>{c.remote_addr}:{c.remote_port}</TableCell>
                    <TableCell>{c.protocol}</TableCell>
                    <TableCell>{c.state}</TableCell>
                    <TableCell>{c.is_suspicious && <Chip label="suspicious" color="error" size="small" />}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      {tab === 3 && <Timeline processes={processes} />}
      {tab === 4 && <ThreatIndicators yaraMatches={yara_matches} mlFindings={ml_findings} />}
    </Box>
  );
}
