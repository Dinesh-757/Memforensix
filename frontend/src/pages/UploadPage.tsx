import React, { useCallback, useState } from "react";
import {
  Box, Paper, Typography, Button, LinearProgress, Alert, Stack, Chip,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { useNavigate } from "react-router-dom";
import { analysisApi } from "@/services/api";

const ACCEPTED_EXT = [".raw", ".dmp", ".mem", ".vmem", ".elf", ".core"];

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadPct, setUploadPct] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const validateAndSet = (f: File) => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXT.includes(ext)) {
      setError(`Unsupported file type. Accepted: ${ACCEPTED_EXT.join(", ")}`);
      return;
    }
    setError(null);
    setFile(f);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.[0]) validateAndSet(e.dataTransfer.files[0]);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const resp = await analysisApi.upload(file, setUploadPct);
      navigate(`/analysis/${resp.data.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Upload Memory Dump</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        sx={{
          p: 6, textAlign: "center", border: "2px dashed",
          borderColor: dragOver ? "#ff0000" : "rgba(139,0,0,0.4)",
          backgroundColor: dragOver ? "rgba(255,0,0,0.05)" : "background.paper",
          transition: "all 0.2s",
        }}
      >
        <CloudUploadIcon sx={{ fontSize: 60, color: "#8b0000", mb: 2 }} />
        <Typography variant="h6" gutterBottom>Drag & drop a memory dump here</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Supported formats: {ACCEPTED_EXT.join(", ")} — max 4GB
        </Typography>

        <Button component="label" variant="outlined" sx={{ mt: 2 }}>
          Browse Files
          <input
            type="file" hidden accept={ACCEPTED_EXT.join(",")}
            onChange={(e) => e.target.files?.[0] && validateAndSet(e.target.files[0])}
          />
        </Button>

        {file && (
          <Stack alignItems="center" spacing={1} sx={{ mt: 3 }}>
            <Chip label={`${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`} color="primary" />
          </Stack>
        )}
      </Paper>

      {uploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={uploadPct} />
          <Typography variant="caption" color="text.secondary">Uploading… {uploadPct}%</Typography>
        </Box>
      )}

      <Button
        variant="contained" size="large" sx={{ mt: 3 }} disabled={!file || uploading}
        onClick={handleUpload}
      >
        Start Analysis
      </Button>
    </Box>
  );
}
