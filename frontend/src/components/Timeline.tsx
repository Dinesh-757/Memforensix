import React from "react";
import { Box, Typography, Paper, Stack, Chip } from "@mui/material";
import { ProcessRecord } from "@/services/api";
import { formatDate } from "@/utils/helpers";

export default function Timeline({ processes }: { processes: ProcessRecord[] }) {
  const sorted = [...processes]
    .filter((p) => p.create_time)
    .sort((a, b) => new Date(a.create_time!).getTime() - new Date(b.create_time!).getTime());

  if (sorted.length === 0) {
    return <Typography color="text.secondary">No timestamped process events available.</Typography>;
  }

  return (
    <Stack spacing={1.5} sx={{ position: "relative", pl: 3, borderLeft: "2px solid #8b0000" }}>
      {sorted.map((p) => (
        <Paper
          key={p.pid}
          sx={{ p: 1.5, position: "relative", "&::before": {
            content: '""', position: "absolute", left: -28, top: 18, width: 10, height: 10,
            borderRadius: "50%", backgroundColor: p.is_suspicious ? "#ff1744" : "#ff0000",
          } }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" fontFamily="monospace">
              {formatDate(p.create_time)} — <strong>{p.name}</strong> (PID {p.pid})
            </Typography>
            {p.is_suspicious && <Chip label="suspicious" color="error" size="small" />}
          </Stack>
        </Paper>
      ))}
    </Stack>
  );
}
