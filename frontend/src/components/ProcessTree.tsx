import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { Box } from "@mui/material";
import { ProcessRecord } from "@/services/api";

interface TreeNode {
  name: string;
  pid: number;
  is_suspicious: boolean;
  children: TreeNode[];
}

function buildTree(processes: ProcessRecord[]): TreeNode[] {
  const byPid = new Map<number, TreeNode>();
  processes.forEach((p) => byPid.set(p.pid, { name: p.name, pid: p.pid, is_suspicious: p.is_suspicious, children: [] }));

  const roots: TreeNode[] = [];
  processes.forEach((p) => {
    const node = byPid.get(p.pid)!;
    if (p.ppid && byPid.has(p.ppid)) {
      byPid.get(p.ppid)!.children.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

export default function ProcessTree({ processes }: { processes: ProcessRecord[] }) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current || processes.length === 0) return;

    const width = 900;
    const height = Math.max(400, processes.length * 30);

    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const roots = buildTree(processes);
    const virtualRoot: TreeNode = { name: "ROOT", pid: -1, is_suspicious: false, children: roots };

    const root = d3.hierarchy(virtualRoot);
    const treeLayout = d3.tree<TreeNode>().size([height - 40, width - 200]);
    treeLayout(root);

    const g = svg.append("g").attr("transform", "translate(80,20)");

    g.selectAll(".link")
      .data(root.links().filter((l) => l.source.data.pid !== -1))
      .join("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", "#8b0000")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.6)
      .attr(
        "d",
        d3
          .linkHorizontal<d3.HierarchyPointLink<TreeNode>, d3.HierarchyPointNode<TreeNode>>()
          .x((d) => d.y)
          .y((d) => d.x) as unknown as string
      );

    const node = g
      .selectAll(".node")
      .data(root.descendants().filter((d) => d.data.pid !== -1))
      .join("g")
      .attr("transform", (d: any) => `translate(${d.y},${d.x})`);

    node
      .append("circle")
      .attr("r", 6)
      .attr("fill", (d: any) => (d.data.is_suspicious ? "#ff1744" : "#ff0000"))
      .attr("stroke", "#1a0a0a")
      .attr("stroke-width", 1.5);

    node
      .append("text")
      .attr("dy", 4)
      .attr("x", 10)
      .attr("fill", "#f5f5f5")
      .style("font-size", "11px")
      .style("font-family", "monospace")
      .text((d: any) => `${d.data.name} (${d.data.pid})`);
  }, [processes]);

  return (
    <Box sx={{ overflowX: "auto", bgcolor: "background.paper", borderRadius: 1, p: 1 }}>
      <svg ref={ref} style={{ width: "100%", minHeight: 400 }} />
    </Box>
  );
}
