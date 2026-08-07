import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { Box } from "@mui/material";
import { NetworkConnection } from "@/services/api";

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  type: "local" | "remote";
  suspicious: boolean;
}
interface GraphLink {
  source: string;
  target: string;
  suspicious: boolean;
}

export default function NetworkGraph({ connections }: { connections: NetworkConnection[] }) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current || connections.length === 0) return;

    const width = 900;
    const height = 500;

    const nodesMap = new Map<string, GraphNode>();
    const links: GraphLink[] = [];

    connections.forEach((c) => {
      const localId = `${c.process_name ?? "proc"}:${c.local_port ?? "?"}`;
      const remoteId = `${c.remote_addr ?? "?"}:${c.remote_port ?? "?"}`;
      if (!nodesMap.has(localId)) nodesMap.set(localId, { id: localId, type: "local", suspicious: c.is_suspicious });
      if (!nodesMap.has(remoteId)) nodesMap.set(remoteId, { id: remoteId, type: "remote", suspicious: c.is_suspicious });
      links.push({ source: localId, target: remoteId, suspicious: c.is_suspicious });
    });

    const nodes = Array.from(nodesMap.values());

    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink<GraphNode, any>(links).id((d) => d.id).distance(140))
      .force("charge", d3.forceManyBody().strength(-250))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => (d.suspicious ? "#ff1744" : "#8b0000"))
      .attr("stroke-width", (d) => (d.suspicious ? 2.5 : 1.5))
      .attr("opacity", 0.7);

    const node = svg
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (d) => (d.type === "local" ? 8 : 6))
      .attr("fill", (d) => (d.suspicious ? "#ff1744" : d.type === "local" ? "#ff0000" : "#666"))
      .attr("stroke", "#1a0a0a")
      .attr("stroke-width", 1.5)
      .call(
        (d3
          .drag<SVGCircleElement, GraphNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })) as any
      );

    const label = svg
      .append("g")
      .selectAll("text")
      .data(nodes)
      .join("text")
      .text((d) => d.id)
      .attr("font-size", 9)
      .attr("fill", "#f5f5f5")
      .attr("font-family", "monospace")
      .attr("dx", 10)
      .attr("dy", 4);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);
      node.attr("cx", (d) => d.x!).attr("cy", (d) => d.y!);
      label.attr("x", (d) => d.x!).attr("y", (d) => d.y!);
    });

    return () => { simulation.stop(); };
  }, [connections]);

  return (
    <Box sx={{ overflowX: "auto", bgcolor: "background.paper", borderRadius: 1, p: 1 }}>
      <svg ref={ref} style={{ width: "100%", minHeight: 500 }} />
    </Box>
  );
}
