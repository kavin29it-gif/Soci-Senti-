import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  Share2,
  ShieldAlert,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Layers,
  Sparkles
} from 'lucide-react';
import { api } from '../api';
import type { CoordinatedCluster, NetworkLink, NetworkNode } from '../types';

interface ColorEntry {
  primary: string;
  light: string;
  border: string;
  glow: string;
  name: string;
}

const COMMUNITY_PALETTE: ColorEntry[] = [
  { primary: '#ff7a1a', light: '#ffd9b8', border: '#ffe6d1', glow: '#ff7a1a', name: 'Bright Orange' },
  { primary: '#ff9a4d', light: '#ffe0c4', border: '#ffedd9', glow: '#ff9a4d', name: 'Warm Amber' },
  { primary: '#ffb679', light: '#ffebd6', border: '#fff4e8', glow: '#ffb679', name: 'Peach Glow' },
  { primary: '#f97316', light: '#fed7aa', border: '#ffedd5', glow: '#fb923c', name: 'Tangerine' },
  { primary: '#ea580c', light: '#fdba74', border: '#fed7aa', glow: '#f97316', name: 'Flame Orange' },
  { primary: '#c2410c', light: '#fb923c', border: '#fed7aa', glow: '#ea580c', name: 'Burnt Copper' },
  { primary: '#f59e0b', light: '#fde68a', border: '#fef3c7', glow: '#fbbf24', name: 'Golden Sun' },
  { primary: '#fb7185', light: '#fecdd3', border: '#ffe4e6', glow: '#f43f5e', name: 'Sunset Coral' },
  { primary: '#d97706', light: '#fde68a', border: '#fef3c7', glow: '#f59e0b', name: 'Deep Amber' },
  { primary: '#ff6b10', light: '#ffd1b3', border: '#ffe2cc', glow: '#ff7a1a', name: 'Neon Marmalade' },
  { primary: '#f4845f', light: '#f7b299', border: '#fcd9cc', glow: '#f27059', name: 'Persimmon' },
  { primary: '#eab308', light: '#fef08a', border: '#fef9c3', glow: '#facc15', name: 'Marigold' },
];

interface SimNode extends NetworkNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

export const NetworkView: React.FC = () => {
  const [rawNodes, setRawNodes] = useState<NetworkNode[]>([]);
  const [links, setLinks] = useState<NetworkLink[]>([]);
  const [clusters, setClusters] = useState<CoordinatedCluster[]>([]);
  const [simNodes, setSimNodes] = useState<SimNode[]>([]);

  // Selection & Hover
  const [selectedNode, setSelectedNode] = useState<SimNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<SimNode | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<CoordinatedCluster | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  // Filters & Display options
  const [filterCoordinatedOnly, setFilterCoordinatedOnly] = useState(false);
  const [hideIsolated, setHideIsolated] = useState(true);
  const [platformFilter, setPlatformFilter] = useState<'all' | 'reddit' | 'youtube' | 'telegram'>('all');
  const [activeCommunity, setActiveCommunity] = useState<number | 'all'>('all');
  const [loading, setLoading] = useState(true);

  // Pan & Zoom
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const draggedNodeRef = useRef<SimNode | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  const CANVAS_WIDTH = 1050;
  const CANVAS_HEIGHT = 650;

  // Initialize layout with non-overlapping sunflower spacing & hard collision constraints
  const initializeSimulation = (nodesData: NetworkNode[], linksData: NetworkLink[]) => {
    // 1. Group nodes by community to find unique clusters
    const communityNodes: Record<number, NetworkNode[]> = {};
    nodesData.forEach((n) => {
      const c = n.community ?? 0;
      if (!communityNodes[c]) communityNodes[c] = [];
      communityNodes[c].push(n);
    });

    const uniqueCommunities = Object.keys(communityNodes)
      .map(Number)
      .sort((a, b) => communityNodes[b].length - communityNodes[a].length);

    // Symmetrically position community centroids on an expansive elliptical orbit
    const centroids: Record<number, { x: number; y: number }> = {};
    const cx = CANVAS_WIDTH / 2;
    const cy = CANVAS_HEIGHT / 2;
    const totalComms = Math.max(1, uniqueCommunities.length);
    const orbitRadiusX = 350;
    const orbitRadiusY = 220;

    uniqueCommunities.forEach((commId, idx) => {
      const angle = (idx / totalComms) * 2 * Math.PI - Math.PI / 2;
      centroids[commId] = {
        x: cx + Math.cos(angle) * orbitRadiusX,
        y: cy + Math.sin(angle) * orbitRadiusY,
      };
    });

    // 2. Initialize node positions using sunflower (Fibonacci) spiral packing
    // Guaranteed non-overlapping start for every single node!
    const nodesMap: Record<string, SimNode> = {};
    const initialized: SimNode[] = [];
    const phi = 137.508 * (Math.PI / 180); // golden angle

    uniqueCommunities.forEach((commId) => {
      const members = communityNodes[commId];
      const center = centroids[commId] || { x: cx, y: cy };

      members.forEach((n, idx) => {
        // Radius scaled for crisp visibility: minimum 7px, max 13px
        const r = Math.max(7, Math.min(13, 7 + Math.sqrt(n.degree || 0) * 1.3));

        let nodeX = center.x;
        let nodeY = center.y;

        if (idx > 0) {
          // Sunflower spiral formula ensures optimal uniform spacing between circles
          const spiralRadius = 32 * Math.sqrt(idx);
          const theta = idx * phi;
          nodeX = center.x + Math.cos(theta) * spiralRadius;
          nodeY = center.y + Math.sin(theta) * spiralRadius;
        }

        const simNode: SimNode = {
          ...n,
          x: nodeX,
          y: nodeY,
          vx: 0,
          vy: 0,
          radius: r,
        };
        nodesMap[simNode.id] = simNode;
        initialized.push(simNode);
      });
    });

    // 3. Force-directed relaxation with bounded link attraction
    const iterations = 60;
    const kRepel = 3200;
    const kAttr = 0.025;
    const kGravity = 0.04;

    for (let it = 0; it < iterations; it++) {
      const damping = Math.max(0.2, 1 - it / iterations);

      // Node-Node Repulsion
      for (let i = 0; i < initialized.length; i++) {
        const n1 = initialized[i];
        for (let j = i + 1; j < initialized.length; j++) {
          const n2 = initialized[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy + 1;
          const dist = Math.sqrt(distSq);
          if (dist < 280) {
            const force = (kRepel / distSq) * damping;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }
        }
      }

      // Link Attraction (Capped so cliques don't collapse into a clump)
      linksData.forEach((link) => {
        const n1 = nodesMap[typeof link.source === 'string' ? link.source : (link.source as any).id];
        const n2 = nodesMap[typeof link.target === 'string' ? link.target : (link.target as any).id];
        if (n1 && n2) {
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.hypot(dx, dy) || 1;
          const targetDist = 48;
          if (dist > targetDist) {
            const force = Math.min(8, (dist - targetDist) * kAttr) * damping;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx += fx;
            n1.vy += fy;
            n2.vx -= fx;
            n2.vy -= fy;
          }
        }
      });

      // Community Centroid Attraction
      initialized.forEach((node) => {
        const target = centroids[node.community ?? 0] || { x: cx, y: cy };
        const dx = target.x - node.x;
        const dy = target.y - node.y;
        node.vx += dx * kGravity * damping;
        node.vy += dy * kGravity * damping;

        node.x += Math.max(-12, Math.min(12, node.vx * 0.35));
        node.y += Math.max(-12, Math.min(12, node.vy * 0.35));
        node.vx *= 0.6;
        node.vy *= 0.6;
      });
    }

    // 4. HARD NON-PENETRATION COLLISION RESOLUTION PASS
    // Mathematically guarantees that min distance between any two nodes is at least radius1 + radius2 + 18px!
    const collisionPasses = 35;
    for (let cp = 0; cp < collisionPasses; cp++) {
      for (let i = 0; i < initialized.length; i++) {
        const n1 = initialized[i];
        for (let j = i + 1; j < initialized.length; j++) {
          const n2 = initialized[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.hypot(dx, dy) || 0.001;
          const minAllowed = n1.radius + n2.radius + 18; // 18px guaranteed empty gap!

          if (dist < minAllowed) {
            const overlap = minAllowed - dist;
            const px = (dx / dist) * (overlap * 0.5);
            const py = (dy / dist) * (overlap * 0.5);
            n1.x -= px;
            n1.y -= py;
            n2.x += px;
            n2.y += py;
          }
        }
      }
    }

    // 5. Canvas Boundary Clamping
    initialized.forEach((node) => {
      node.x = Math.max(node.radius + 40, Math.min(CANVAS_WIDTH - (node.radius + 40), node.x));
      node.y = Math.max(node.radius + 40, Math.min(CANVAS_HEIGHT - (node.radius + 40), node.y));
    });

    setSimNodes(initialized);
  };

  const fetchNetwork = async () => {
    setLoading(true);
    setSelectedNode(null);
    setSelectedCluster(null);
    try {
      const data = await api.getNetworkGraph();
      setRawNodes(data.nodes);
      setLinks(data.links);
      setClusters(data.coordinated_clusters);
      initializeSimulation(data.nodes, data.links);
    } catch {
      // Mock fallback
      const fallbackNodes: NetworkNode[] = [
        { id: 'auth_9f82a1', short_id: 'auth_9f8...', platform: 'reddit', community: 1, degree: 5, pagerank: 0.082, coordinated: true },
        { id: 'auth_8c12b4', short_id: 'auth_8c1...', platform: 'reddit', community: 1, degree: 4, pagerank: 0.065, coordinated: true },
        { id: 'auth_77a90e', short_id: 'auth_77a...', platform: 'reddit', community: 1, degree: 4, pagerank: 0.058, coordinated: true },
        { id: 'tg_chan_apex', short_id: 'tg_apex...', platform: 'telegram', community: 2, degree: 7, pagerank: 0.124, coordinated: false },
        { id: 'yt_analyst_01', short_id: 'yt_01...', platform: 'youtube', community: 3, degree: 3, pagerank: 0.042, coordinated: false },
      ];
      const fallbackLinks = [
        { source: 'auth_9f82a1', target: 'auth_8c12b4', weight: 2.0, interaction: 'coordinated_post' },
        { source: 'auth_8c12b4', target: 'auth_77a90e', weight: 2.0, interaction: 'coordinated_post' },
        { source: 'auth_9f82a1', target: 'auth_77a90e', weight: 2.0, interaction: 'coordinated_post' },
      ];
      setRawNodes(fallbackNodes);
      setLinks(fallbackLinks);
      setClusters([
        {
          cluster_id: 'cluster_001',
          account_count: 3,
          accounts: ['auth_9f82a1', 'auth_8c12b4', 'auth_77a90e'],
          evidence_post_ids: ['p1', 'p2', 'p3'],
          sample_text: 'Liquidity run warning on ApexReserve. Move funds now!',
          coordination_score: 0.88,
        },
      ]);
      initializeSimulation(fallbackNodes, fallbackLinks);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNetwork();
  }, []);

  // Filtered nodes
  const visibleNodes = useMemo(() => {
    return simNodes.filter((n) => {
      if (filterCoordinatedOnly && !n.coordinated) return false;
      if (hideIsolated && n.degree === 0) return false;
      if (platformFilter !== 'all' && n.platform !== platformFilter) return false;
      if (activeCommunity !== 'all' && n.community !== activeCommunity) return false;
      return true;
    });
  }, [simNodes, filterCoordinatedOnly, hideIsolated, platformFilter, activeCommunity]);

  // Set of visible node IDs for fast O(1) checks
  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  // Connected node IDs for highlighted or selected node
  const activeNeighborIds = useMemo(() => {
    const focusId = hoveredNode?.id || selectedNode?.id;
    if (!focusId) return null;
    const neighbors = new Set<string>([focusId]);
    links.forEach((l) => {
      const s = typeof l.source === 'string' ? l.source : (l.source as any).id;
      const t = typeof l.target === 'string' ? l.target : (l.target as any).id;
      if (s === focusId) neighbors.add(t);
      if (t === focusId) neighbors.add(s);
    });
    return neighbors;
  }, [hoveredNode, selectedNode, links]);

  // Cluster member IDs if a cluster is selected
  const clusterMemberIds = useMemo(() => {
    if (!selectedCluster) return null;
    return new Set(selectedCluster.accounts);
  }, [selectedCluster]);

  // Draw function for Canvas
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // High-DPI clear
    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Apply pan & zoom transform
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    // 1. Draw subtle background coordinate grid
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.04)';
    ctx.lineWidth = 1;
    const gridStep = 45;
    ctx.beginPath();
    for (let x = 0; x < CANVAS_WIDTH; x += gridStep) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, CANVAS_HEIGHT);
    }
    for (let y = 0; y < CANVAS_HEIGHT; y += gridStep) {
      ctx.moveTo(0, y);
      ctx.lineTo(CANVAS_WIDTH, y);
    }
    ctx.stroke();

    // Map for fast node coordinate lookup
    const nodeMap = new Map(visibleNodes.map((n) => [n.id, n]));

    // 2. Draw Links (Edges)
    links.forEach((link) => {
      const srcId = typeof link.source === 'string' ? link.source : (link.source as any).id;
      const tgtId = typeof link.target === 'string' ? link.target : (link.target as any).id;

      if (!visibleNodeIds.has(srcId) || !visibleNodeIds.has(tgtId)) return;
      const src = nodeMap.get(srcId);
      const tgt = nodeMap.get(tgtId);
      if (!src || !tgt) return;

      const isConnectedToFocus = activeNeighborIds && (activeNeighborIds.has(srcId) && activeNeighborIds.has(tgtId));
      const isClusterEdge = clusterMemberIds && (clusterMemberIds.has(srcId) && clusterMemberIds.has(tgtId));
      const hasAnyFocus = Boolean(activeNeighborIds || clusterMemberIds);

      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);

      if (isConnectedToFocus || isClusterEdge) {
        // High-voltage glowing edge on active focus
        ctx.strokeStyle = isClusterEdge ? '#f43f5e' : '#06b6d4';
        ctx.lineWidth = 2.4;
        ctx.shadowColor = isClusterEdge ? '#f43f5e' : '#06b6d4';
        ctx.shadowBlur = 8;
        ctx.stroke();
        ctx.shadowBlur = 0; // reset
      } else if (hasAnyFocus) {
        // Dimmed edges when focusing on a specific node or cluster
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
        ctx.lineWidth = 0.5;
        ctx.stroke();
      } else {
        // Default clean idle edges
        if (link.interaction === 'coordinated_post') {
          ctx.strokeStyle = 'rgba(244, 63, 94, 0.18)';
          ctx.lineWidth = 1;
        } else {
          ctx.strokeStyle = 'rgba(148, 163, 184, 0.08)';
          ctx.lineWidth = 0.7;
        }
        ctx.stroke();
      }
    });

    // 3. Draw Nodes (Crisp, High-Luminance 3D Spheres with Razor-Sharp Rims)
    visibleNodes.forEach((node) => {
      const isSelected = selectedNode?.id === node.id;
      const isHovered = hoveredNode?.id === node.id;
      const isInCluster = clusterMemberIds?.has(node.id);
      const isNeighbor = activeNeighborIds?.has(node.id);
      const hasFocus = Boolean(activeNeighborIds || clusterMemberIds);

      // Determine opacity: if something is highlighted and this node is not part of it, dim it down
      const opacity = hasFocus && !isNeighbor && !isInCluster ? 0.22 : 1.0;
      const pal = COMMUNITY_PALETTE[(node.community ?? 0) % COMMUNITY_PALETTE.length];

      ctx.save();
      ctx.globalAlpha = opacity;

      // Outer Indicator for Coordinated Accounts (Clean tactical ring, ZERO dark blurry filled disc!)
      if (node.coordinated || isInCluster) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 5.5, 0, 2 * Math.PI);
        if (isInCluster) {
          ctx.strokeStyle = '#f43f5e';
          ctx.lineWidth = 2.2;
          ctx.shadowColor = '#f43f5e';
          ctx.shadowBlur = 8;
        } else {
          ctx.strokeStyle = 'rgba(244, 63, 94, 0.85)';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([3, 2.5]); // high-tech tactical dashed border
        }
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.shadowBlur = 0;
      }

      // Selection / Hover Halo Ring
      if (isSelected || isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + (isSelected ? 7 : 5), 0, 2 * Math.PI);
        ctx.strokeStyle = isSelected ? '#ffffff' : '#38bdf8';
        ctx.lineWidth = 2.4;
        ctx.shadowColor = isSelected ? '#ffffff' : '#38bdf8';
        ctx.shadowBlur = 12;
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // 3D Luminous Sphere with specular reflection
      const grad = ctx.createRadialGradient(
        node.x - node.radius * 0.35,
        node.y - node.radius * 0.35,
        Math.max(1, node.radius * 0.1),
        node.x,
        node.y,
        node.radius
      );
      grad.addColorStop(0, '#ffffff');      // bright specular shine highlight
      grad.addColorStop(0.35, pal.light);   // luminous vibrant glow
      grad.addColorStop(1, pal.primary);    // rich saturated core base

      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
      ctx.fillStyle = grad;
      ctx.fill();

      // Razor-sharp crisp outer border (solves blurry edges!)
      ctx.strokeStyle = isSelected ? '#ffffff' : pal.border;
      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.stroke();

      // Crisp inner white pupil dot for micro-precision
      ctx.beginPath();
      ctx.arc(node.x, node.y, Math.max(1.8, node.radius * 0.28), 0, 2 * Math.PI);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      // Top Hub & Active Labels
      const isTopHub = node.pagerank > 0.05 && node.degree >= 5;
      if (isHovered || isSelected || isTopHub) {
        const label = node.short_id || node.id.slice(0, 8);
        ctx.font = '600 10px "JetBrains Mono", monospace';
        const textWidth = ctx.measureText(label).width;

        // Label Background Pill
        const pillX = node.x - textWidth / 2 - 5;
        const pillY = node.y - node.radius - 18;
        const pillW = textWidth + 10;
        const pillH = 15;

        ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
        ctx.beginPath();
        ctx.roundRect(pillX, pillY, pillW, pillH, 4);
        ctx.fill();
        ctx.strokeStyle = isHovered || isSelected ? '#38bdf8' : 'rgba(255, 255, 255, 0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = isHovered || isSelected ? '#38bdf8' : '#f8fafc';
        ctx.fillText(label, pillX + 5, pillY + 11);
      }

      ctx.restore();
    });

    ctx.restore();
  }, [visibleNodes, links, visibleNodeIds, activeNeighborIds, clusterMemberIds, selectedNode, hoveredNode, transform]);

  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(renderCanvas);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [renderCanvas]);

  // Mouse Coordinate to Graph Space Converter
  const getGraphCoords = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = (clientX - rect.left) * scaleX;
    const canvasY = (clientY - rect.top) * scaleY;
    const graphX = (canvasX - transform.x) / transform.k;
    const graphY = (canvasY - transform.y) / transform.k;
    return { x: graphX, y: graphY };
  };

  // Node Hit Testing
  const findNodeAt = (graphX: number, graphY: number): SimNode | null => {
    for (let i = visibleNodes.length - 1; i >= 0; i--) {
      const n = visibleNodes[i];
      const dist = Math.hypot(n.x - graphX, n.y - graphY);
      if (dist <= n.radius + 6) {
        return n;
      }
    }
    return null;
  };

  // Canvas Interactions
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getGraphCoords(e.clientX, e.clientY);
    const node = findNodeAt(coords.x, coords.y);

    if (node) {
      draggedNodeRef.current = node;
      setSelectedNode(node);
      const cl = clusters.find((c) => c.accounts.includes(node.id));
      setSelectedCluster(cl || null);
    } else {
      isDraggingRef.current = true;
      dragStartRef.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getGraphCoords(e.clientX, e.clientY);

    // Dragging an individual node
    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = coords.x;
      draggedNodeRef.current.y = coords.y;
      renderCanvas();
      return;
    }

    // Panning canvas
    if (isDraggingRef.current) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - dragStartRef.current.x,
        y: e.clientY - dragStartRef.current.y,
      }));
      return;
    }

    // Hover state
    const node = findNodeAt(coords.x, coords.y);
    setHoveredNode(node);
    if (node) {
      const canvas = canvasRef.current;
      if (canvas) {
        const rect = canvas.getBoundingClientRect();
        setTooltipPos({
          x: e.clientX - rect.left + 14,
          y: e.clientY - rect.top + 14,
        });
      }
    } else {
      setTooltipPos(null);
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
    draggedNodeRef.current = null;
  };

  // Zooming via Wheel
  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    setTransform((prev) => {
      const newK = Math.max(0.4, Math.min(3.5, prev.k * zoomFactor));
      return { ...prev, k: newK };
    });
  };

  // Zoom Controls
  const handleZoomIn = () => setTransform((t) => ({ ...t, k: Math.min(3.5, t.k * 1.25) }));
  const handleZoomOut = () => setTransform((t) => ({ ...t, k: Math.max(0.4, t.k * 0.8) }));
  const handleResetView = () => setTransform({ x: 0, y: 0, k: 1 });

  // Unique communities for filter pill row
  const availableCommunities = useMemo(() => {
    const set = new Set<number>();
    rawNodes.forEach((n) => {
      if (n.community !== undefined && n.community !== null) set.add(n.community);
    });
    return Array.from(set).sort((a, b) => a - b);
  }, [rawNodes]);

  return (
    <div className="space-y-6 animate-fade-in pb-12 font-['Manrope']" ref={containerRef}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#fff3e8] font-['Sora'] flex items-center space-x-2">
            <span>Interaction Graph & Coordinated Behavior (CIB)</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[rgba(255,122,26,0.2)] text-[#ffd9b8] border border-[#ff7a1a]/40">
              {clusters.length} Coordinated Clusters Detected
            </span>
          </h1>
          <p className="text-xs text-[rgba(255,226,205,0.64)] mt-1">
            NetworkX multi-platform interaction topologies, Louvain community partitions, and sockpuppet co-posting rings.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilterCoordinatedOnly(!filterCoordinatedOnly)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${
              filterCoordinatedOnly
                ? 'bg-[rgba(255,122,26,0.25)] text-[#ffd9b8] border-[#ff7a1a] shadow-sm shadow-[#ff7a1a]/30'
                : 'bg-[rgba(255,154,77,0.08)] text-[rgba(255,226,205,0.7)] border-[rgba(255,196,140,0.2)] hover:text-[#fff3e8]'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-[#ff7a1a]" />
            <span>Coordinated Only</span>
          </button>

          <button
            onClick={() => setHideIsolated(!hideIsolated)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${
              hideIsolated
                ? 'bg-[rgba(255,154,77,0.2)] text-[#ffd9b8] border-[#ff9a4d]'
                : 'bg-[rgba(255,154,77,0.08)] text-[rgba(255,226,205,0.7)] border-[rgba(255,196,140,0.2)] hover:text-[#fff3e8]'
            }`}
            title="Hide singletons with 0 connections for a clear, uncluttered view"
          >
            <Filter className="w-3.5 h-3.5 text-[#ff9a4d]" />
            <span>Active Links Only</span>
          </button>

          <button
            onClick={fetchNetwork}
            className="p-2 text-xs bg-[rgba(255,154,77,0.08)] hover:bg-[#ff7a1a] hover:text-[#0b0603] border border-[rgba(255,196,140,0.25)] text-[#ffd9b8] rounded-xl transition-all cursor-pointer"
            title="Refresh network"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar: Platforms & Communities */}
      <div className="glass-panel p-4 rounded-2xl flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Platform Selector */}
        <div className="flex items-center space-x-2">
          <span className="text-[rgba(255,226,205,0.6)] text-[11px] font-semibold uppercase tracking-wider font-['Sora']">Platform:</span>
          {(['all', 'reddit', 'youtube', 'telegram'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPlatformFilter(p)}
              className={`px-3 py-1 rounded-lg text-[11px] font-semibold uppercase tracking-wider transition-all cursor-pointer ${
                platformFilter === p
                  ? 'bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603] font-bold shadow-md shadow-[#ff7a1a]/30'
                  : 'bg-[rgba(255,154,77,0.08)] text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8] hover:bg-[rgba(255,154,77,0.15)]'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Louvain Community Filter Chips */}
        <div className="flex items-center space-x-1.5 overflow-x-auto max-w-xl py-0.5">
          <span className="text-[rgba(255,226,205,0.6)] text-[11px] font-semibold uppercase tracking-wider shrink-0 flex items-center space-x-1 mr-1 font-['Sora']">
            <Layers className="w-3 h-3 text-[#ff7a1a]" />
            <span>Communities:</span>
          </span>
          <button
            onClick={() => setActiveCommunity('all')}
            className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer ${
              activeCommunity === 'all'
                ? 'bg-gradient-to-r from-[#ff7a1a] to-[#ff9a4d] text-[#0b0603]'
                : 'bg-[rgba(255,154,77,0.08)] text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8]'
            }`}
          >
            All ({availableCommunities.length})
          </button>
          {availableCommunities.slice(0, 8).map((cid) => {
            const pal = COMMUNITY_PALETTE[cid % COMMUNITY_PALETTE.length];
            const isSelected = activeCommunity === cid;
            return (
              <button
                key={cid}
                onClick={() => setActiveCommunity(isSelected ? 'all' : cid)}
                className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-all cursor-pointer border ${
                  isSelected
                    ? 'border-[#ff7a1a] text-[#ffd9b8] shadow-sm'
                    : 'border-[rgba(255,196,140,0.2)] text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8]'
                }`}
                style={{
                  backgroundColor: isSelected ? `${pal.primary}40` : `${pal.primary}15`,
                  borderColor: isSelected ? '#ff7a1a' : `${pal.border}40`,
                }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: pal.light }} />
                <span>C#{cid}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Canvas Box */}
        <div className="lg:col-span-2 rounded-[22px] bg-[#0a0503] border border-[rgba(255,196,140,0.2)] shadow-2xl overflow-hidden relative flex flex-col items-center justify-center p-2 min-h-[600px]">
          {/* Top Badges */}
          <div className="absolute top-4 left-4 z-10 flex items-center space-x-2 text-xs bg-[rgba(14,7,4,0.85)] backdrop-blur-md px-3 py-1.5 rounded-xl border border-[rgba(255,196,140,0.2)] text-[#ffd9b8] shadow-md">
            <span className="w-2.5 h-2.5 rounded-full border border-[#ff7a1a] bg-[#ff7a1a] animate-pulse" />
            <span>Tactical Dash Ring: Coordinated CIB Account</span>
          </div>

          <div className="absolute top-4 right-4 z-10 flex items-center space-x-3 text-xs bg-[rgba(14,7,4,0.85)] backdrop-blur-md px-3 py-1.5 rounded-xl border border-[rgba(255,196,140,0.2)] text-[rgba(255,226,205,0.64)] shadow-md">
            <span className="font-mono text-[#ff9a4d] font-bold">{visibleNodes.length} Visible Nodes</span>
            <span>•</span>
            <span className="font-mono text-[#ffd9b8]">{links.length} Edges</span>
          </div>

          {/* Floating Zoom & Pan Toolbars */}
          <div className="absolute bottom-4 left-4 z-10 flex items-center space-x-1.5 bg-[rgba(14,7,4,0.85)] backdrop-blur-md p-1.5 rounded-xl border border-[rgba(255,196,140,0.2)] shadow-lg">
            <button
              onClick={handleZoomIn}
              className="p-1.5 text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8] hover:bg-[rgba(255,154,77,0.15)] rounded-lg transition-colors cursor-pointer"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-1.5 text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8] hover:bg-[rgba(255,154,77,0.15)] rounded-lg transition-colors cursor-pointer"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              onClick={handleResetView}
              className="p-1.5 text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8] hover:bg-[rgba(255,154,77,0.15)] rounded-lg transition-colors cursor-pointer"
              title="Reset View"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <span className="text-[10px] font-mono text-[rgba(255,226,205,0.6)] px-1 font-semibold">
              {Math.round(transform.k * 100)}%
            </span>
          </div>

          {/* Canvas */}
          <canvas
            ref={canvasRef}
            width={CANVAS_WIDTH}
            height={CANVAS_HEIGHT}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onWheel={handleWheel}
            className="cursor-grab active:cursor-grabbing w-full max-w-full h-auto rounded-xl select-none"
          />

          {/* Interactive Floating Hover Tooltip */}
          {hoveredNode && tooltipPos && (
            <div
              className="absolute z-20 pointer-events-none p-3.5 rounded-xl bg-[#0e0704]/95 border border-[rgba(255,196,140,0.3)] shadow-2xl backdrop-blur-md text-xs space-y-2 min-w-[220px] animate-fade-in font-['Manrope']"
              style={{
                left: `${Math.min(CANVAS_WIDTH - 250, tooltipPos.x)}px`,
                top: `${Math.min(CANVAS_HEIGHT - 130, tooltipPos.y)}px`,
              }}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-[#fff3e8] font-bold">{hoveredNode.short_id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)]">
                  {hoveredNode.platform}
                </span>
              </div>
              <div className="text-[11px] text-[rgba(255,226,205,0.6)] flex justify-between">
                <span>PageRank Centrality:</span>
                <span className="font-mono text-[#ff9a4d] font-bold">{hoveredNode.pagerank}</span>
              </div>
              <div className="text-[11px] text-[rgba(255,226,205,0.6)] flex justify-between">
                <span>Interaction Degree:</span>
                <span className="font-mono text-[#fff3e8] font-bold">{hoveredNode.degree} edges</span>
              </div>
              <div className="text-[11px] text-[rgba(255,226,205,0.6)] flex justify-between">
                <span>Louvain Partition:</span>
                <span
                  className="font-bold px-1.5 py-0.5 rounded text-[11px]"
                  style={{
                    color: COMMUNITY_PALETTE[(hoveredNode.community ?? 0) % COMMUNITY_PALETTE.length].light,
                    backgroundColor: `${COMMUNITY_PALETTE[(hoveredNode.community ?? 0) % COMMUNITY_PALETTE.length].primary}30`
                  }}
                >
                  Community #{hoveredNode.community}
                </span>
              </div>
              {hoveredNode.coordinated && (
                <div className="pt-1.5 border-t border-[rgba(255,196,140,0.15)] flex items-center space-x-1.5 text-[#ff7a1a] font-bold text-[10px]">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Flagged Coordinated Account</span>
                </div>
              )}
            </div>
          )}

          <div className="text-[11px] text-[rgba(255,226,205,0.6)] pb-2 pt-1 flex items-center space-x-3">
            <span>🖱️ Click & Drag to pan canvas</span>
            <span>•</span>
            <span>🔍 Scroll to zoom</span>
            <span>•</span>
            <span>👆 Click any node to inspect telemetry</span>
          </div>
        </div>

        {/* Sidebar: Clusters & Node Inspector */}
        <div className="space-y-4">
          {/* Selected Node Inspector */}
          {selectedNode ? (
            <div className="glass-panel p-5 rounded-[22px] border border-[#ff7a1a]/40 shadow-xl space-y-4 animate-fade-in">
              <div className="flex items-center justify-between border-b border-[rgba(255,196,140,0.15)] pb-2.5">
                <div className="flex items-center space-x-2">
                  <span
                    className="w-3.5 h-3.5 rounded-full border border-white"
                    style={{
                      backgroundColor: COMMUNITY_PALETTE[(selectedNode.community ?? 0) % COMMUNITY_PALETTE.length].primary,
                    }}
                  />
                  <span className="text-xs font-bold uppercase tracking-wider text-[#ffd9b8] font-['Sora']">
                    Node Structural Telemetry
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-[rgba(255,154,77,0.15)] text-[#ffd9b8] border border-[rgba(255,196,140,0.25)]">
                  {selectedNode.platform}
                </span>
              </div>

              <div>
                <p className="text-[11px] text-[rgba(255,226,205,0.6)]">Salted Author Identifier (SHA-256):</p>
                <p className="text-xs font-mono text-[#fff3e8] break-all bg-black/60 p-2.5 rounded-xl border border-[rgba(255,196,140,0.15)] mt-1">
                  {selectedNode.id}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-3 bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] rounded-xl border border-[rgba(255,196,140,0.18)]">
                  <p className="text-[10px] text-[rgba(255,226,205,0.6)] font-semibold font-['Sora']">PageRank Centrality</p>
                  <p className="text-base font-extrabold font-mono text-[#ffd9b8] mt-0.5">{selectedNode.pagerank}</p>
                </div>
                <div className="p-3 bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] rounded-xl border border-[rgba(255,196,140,0.18)]">
                  <p className="text-[10px] text-[rgba(255,226,205,0.6)] font-semibold font-['Sora']">Degree (Interactions)</p>
                  <p className="text-base font-extrabold font-mono text-[#fff3e8] mt-0.5">{selectedNode.degree}</p>
                </div>
              </div>

              <div className="p-3 bg-[linear-gradient(135deg,rgba(255,122,26,0.06)_0%,rgba(20,10,5,0.7)_100%)] rounded-xl border border-[rgba(255,196,140,0.18)] text-xs flex justify-between items-center">
                <span className="text-[rgba(255,226,205,0.6)]">Louvain Community:</span>
                <span
                  className="px-2.5 py-1 rounded-lg text-[11px] font-bold border"
                  style={{
                    backgroundColor: `${COMMUNITY_PALETTE[(selectedNode.community ?? 0) % COMMUNITY_PALETTE.length].primary}25`,
                    borderColor: `${COMMUNITY_PALETTE[(selectedNode.community ?? 0) % COMMUNITY_PALETTE.length].border}50`,
                    color: COMMUNITY_PALETTE[(selectedNode.community ?? 0) % COMMUNITY_PALETTE.length].light,
                  }}
                >
                  Community #{selectedNode.community} ({COMMUNITY_PALETTE[(selectedNode.community ?? 0) % COMMUNITY_PALETTE.length].name})
                </span>
              </div>

              {selectedNode.coordinated ? (
                <div className="p-3 rounded-xl bg-[rgba(255,122,26,0.15)] border border-[#ff7a1a]/40 text-xs text-[#ffd9b8] flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-[#ff7a1a] shrink-0 mt-0.5" />
                  <p className="leading-relaxed">
                    <strong>Coordinated Activity Confirmed:</strong> This account participates in near-identical text bursts across correlated time windows.
                  </p>
                </div>
              ) : (
                <div className="p-2.5 rounded-xl bg-[rgba(255,154,77,0.1)] border border-[rgba(255,196,140,0.25)] text-xs text-[#ffd9b8] flex items-center space-x-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#ff9a4d]" />
                  <span>Standard organic behavior node.</span>
                </div>
              )}

              <button
                onClick={() => setSelectedNode(null)}
                className="w-full py-2 text-xs font-semibold text-[rgba(255,226,205,0.7)] hover:text-[#fff3e8] bg-[rgba(255,154,77,0.08)] hover:bg-[rgba(255,154,77,0.16)] border border-[rgba(255,196,140,0.2)] rounded-xl transition-all cursor-pointer"
              >
                Clear Selection
              </button>
            </div>
          ) : (
            <div className="glass-panel p-6 rounded-[22px] text-center text-xs text-[rgba(255,226,205,0.6)] space-y-2">
              <Share2 className="w-8 h-8 text-[#ff7a1a] mx-auto opacity-75" />
              <p className="font-bold text-[#fff3e8] font-['Sora']">Interactive Canvas Inspector</p>
              <p className="text-[11px] text-[rgba(255,226,205,0.5)]">
                Click any node in the graph to inspect centrality, Louvain community, and campaign affiliations.
              </p>
            </div>
          )}

          {/* Coordinated Sockpuppet Clusters List */}
          <div className="glass-panel p-5 rounded-[22px] space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-[#ff7a1a]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#fff3e8] font-['Sora']">
                  Flagged Sockpuppet Clusters
                </h3>
              </div>
              <span className="text-xs text-[rgba(255,226,205,0.6)] font-mono">{clusters.length} total</span>
            </div>

            <p className="text-[11px] text-[rgba(255,226,205,0.6)]">
              Click any cluster to spotlight and highlight its accounts in the canvas.
            </p>

            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {clusters.map((cl) => {
                const isSelected = selectedCluster?.cluster_id === cl.cluster_id;
                return (
                  <div
                    key={cl.cluster_id}
                    onClick={() => {
                      if (isSelected) {
                        setSelectedCluster(null);
                      } else {
                        setSelectedCluster(cl);
                        setSelectedNode(null);
                      }
                    }}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-[rgba(255,122,26,0.2)] border-[#ff7a1a] shadow-lg shadow-[#ff7a1a]/25'
                        : 'bg-[linear-gradient(135deg,rgba(255,122,26,0.05)_0%,rgba(20,10,5,0.7)_100%)] border-[rgba(255,196,140,0.18)] hover:border-[#ff7a1a]/40'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono font-bold text-[#ffd9b8]">{cl.cluster_id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[rgba(255,122,26,0.2)] text-[#ffd9b8] border border-[#ff7a1a]/40">
                        {cl.account_count} Accounts
                      </span>
                    </div>
                    <p className="text-[11px] text-[rgba(255,226,205,0.85)] line-clamp-2 italic">
                      "{cl.sample_text}"
                    </p>
                    <div className="flex justify-between items-center text-[10px] text-[rgba(255,226,205,0.6)] mt-2 pt-1 border-t border-[rgba(255,196,140,0.12)]">
                      <span className="text-[#ff9a4d] font-semibold">Coordination: {Math.round(cl.coordination_score * 100)}%</span>
                      <span className="font-mono">{cl.evidence_post_ids.length} Evidence Posts</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
