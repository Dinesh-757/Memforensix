import React from "react";
import { Box, LinearProgress, Typography, Paper, Stack, Chip } from "@mui/material";
import { statusColor } from "@/utils/helpers";

export default function ProgressTracker({
  status,
  progress,
  stage,
  message,
}: {
  status: string;
  progress: number;
  stage?: string;
  message?: string;
}) {
  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="subtitle2">Analysis Progress</Typography>
        <Chip label={status} color={statusColor(status)} size="small" />
      </Stack>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 10,
          borderRadius: 5,
          backgroundColor: "rgba(139,0,0,0.2)",
          "& .MuiLinearProgress-bar": {
            background: "linear-gradient(90deg, #8b0000, #ff0000)",
          },
        }}
      />
      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {stage ?? ""} {message ? `— ${message}` : ""}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {progress}%
        </Typography>
      </Box>
    </Paper>
  );
}
