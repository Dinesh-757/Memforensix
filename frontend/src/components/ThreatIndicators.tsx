import React from "react";
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Typography, Box,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { YaraMatch, MLFinding } from "@/services/api";
import { severityColor } from "@/theme";

export default function ThreatIndicators({
  yaraMatches,
  mlFindings,
}: {
  yaraMatches: YaraMatch[];
  mlFindings: MLFinding[];
}) {
  const anomalies = mlFindings.filter((f) => f.is_anomaly);

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <WarningAmberIcon color="error" /> YARA Matches
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 4 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Rule</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Tags</TableCell>
              <TableCell>Matched Strings</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {yaraMatches.length === 0 && (
              <TableRow><TableCell colSpan={4}><Typography color="text.secondary">No YARA matches.</Typography></TableCell></TableRow>
            )}
            {yaraMatches.map((m, idx) => (
              <TableRow key={idx}>
                <TableCell sx={{ fontFamily: "monospace" }}>{m.rule_name}</TableCell>
                <TableCell>
                  <Chip
                    label={m.severity}
                    size="small"
                    sx={{ backgroundColor: severityColor[m.severity] ?? "#666", color: "#fff" }}
                  />
                </TableCell>
                <TableCell>{(m.tags ?? []).join(", ")}</TableCell>
                <TableCell sx={{ fontFamily: "monospace", fontSize: 12 }}>
                  {(m.strings_matched ?? []).join(", ")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" gutterBottom sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <WarningAmberIcon color="warning" /> ML Anomaly Findings
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Entity</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Anomaly Score</TableCell>
              <TableCell>Explanation</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {anomalies.length === 0 && (
              <TableRow><TableCell colSpan={4}><Typography color="text.secondary">No anomalies detected.</Typography></TableCell></TableRow>
            )}
            {anomalies.map((f, idx) => (
              <TableRow key={idx}>
                <TableCell sx={{ fontFamily: "monospace" }}>{f.entity_ref}</TableCell>
                <TableCell>{f.entity_type}</TableCell>
                <TableCell>
                  <Chip
                    label={f.anomaly_score.toFixed(2)}
                    size="small"
                    color={f.anomaly_score > 0.6 ? "error" : "warning"}
                  />
                </TableCell>
                <TableCell>{f.explanation}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
