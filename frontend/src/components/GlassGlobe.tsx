import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Pause, Play } from 'lucide-react';

interface City {
  name: string;
  lat: number;
  lon: number;
}

const GLOBAL_CITIES: City[] = [
  { name: 'New York', lat: 40.71, lon: -74.0 },
  { name: 'London', lat: 51.5, lon: -0.12 },
  { name: 'Tokyo', lat: 35.67, lon: 139.65 },
  { name: 'Singapore', lat: 1.35, lon: 103.81 },
  { name: 'Dubai', lat: 25.2, lon: 55.27 },
  { name: 'Frankfurt', lat: 50.11, lon: 8.68 },
  { name: 'San Francisco', lat: 37.77, lon: -122.41 },
  { name: 'Sydney', lat: -33.86, lon: 151.2 },
  { name: 'São Paulo', lat: -23.55, lon: -46.63 },
];

const FLIGHT_ARCS: [number, number][] = [
  [0, 1], // NYC -> London
  [1, 5], // London -> Frankfurt
  [5, 4], // Frankfurt -> Dubai
  [4, 3], // Dubai -> Singapore
  [3, 2], // Singapore -> Tokyo
  [2, 7], // Tokyo -> Sydney
  [6, 0], // SF -> NYC
  [0, 8], // NYC -> Sao Paulo
];

// Determine if a lat/lon point is roughly over real Earth continent landmass
function isLandmass(lat: number, lon: number): boolean {
  // North America
  if (lat > 15 && lat < 72 && lon > -168 && lon < -52) {
    if (lat < 30 && lon < -105) return false;
    return true;
  }
  // South America
  if (lat > -55 && lat < 12 && lon > -82 && lon < -34) return true;
  // Europe
  if (lat > 36 && lat < 71 && lon > -10 && lon < 45) return true;
  // Africa
  if (lat > -35 && lat < 37 && lon > -18 && lon < 52) return true;
  // Asia
  if (lat > 5 && lat < 75 && lon > 45 && lon < 180) {
    if (lat > 60 && lon > 170) return false;
    return true;
  }
  // Australia & NZ
  if (lat > -44 && lat < -10 && lon > 112 && lon < 178) return true;
  return false;
}

export const GlassGlobe: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return true;
  });

  const stateRef = useRef({
    yaw: 0.8,
    pitch: 0.38,
    targetYaw: 0.8,
    targetPitch: 0.38,
    isDragging: false,
    lastX: 0,
    lastY: 0,
    animFrame: 0,
    arcProgress: 0,
  });

  // Pre-generate continent surface dots on unit sphere
  const globePoints = useRef<{ x: number; y: number; z: number; isLand: boolean }[]>([]);

  useEffect(() => {
    if (globePoints.current.length === 0) {
      const pts: { x: number; y: number; z: number; isLand: boolean }[] = [];
      const latSteps = 72;
      const lonSteps = 144;

      for (let i = 0; i < latSteps; i++) {
        const lat = -85 + (i * 170) / (latSteps - 1);
        const phi = (90 - lat) * (Math.PI / 180);

        for (let j = 0; j < lonSteps; j++) {
          const lon = -180 + (j * 360) / lonSteps;
          const theta = (lon + 180) * (Math.PI / 180);

          const isLand = isLandmass(lat, lon);
          // Keep mostly land points with a few sparse ocean grid lines for elegance
          if (isLand || (i % 6 === 0 && j % 8 === 0)) {
            const x = Math.sin(phi) * Math.cos(theta);
            const y = Math.cos(phi);
            const z = Math.sin(phi) * Math.sin(theta);
            pts.push({ x, y, z, isLand });
          }
        }
      }
      globePoints.current = pts;
    }
  }, []);

  // Handle visibility change (auto-pause on hidden tab to save battery/GPU)
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'hidden') {
        setIsPlaying(false);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, []);

  // Interactive Drag-to-Rotate handlers
  const onPointerDown = useCallback((e: React.PointerEvent) => {
    stateRef.current.isDragging = true;
    stateRef.current.lastX = e.clientX;
    stateRef.current.lastY = e.clientY;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!stateRef.current.isDragging) return;
    const dx = e.clientX - stateRef.current.lastX;
    const dy = e.clientY - stateRef.current.lastY;
    stateRef.current.lastX = e.clientX;
    stateRef.current.lastY = e.clientY;

    stateRef.current.yaw += dx * 0.005;
    stateRef.current.pitch = Math.max(-0.8, Math.min(0.8, stateRef.current.pitch + dy * 0.005));
  }, []);

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    stateRef.current.isDragging = false;
    try {
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      // ignore
    }
  }, []);

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let running = true;

    const render = () => {
      if (!running) return;

      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const width = window.innerWidth;
      const height = window.innerHeight;

      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      // Auto-rotation when playing and not user-dragging
      if (isPlaying && !stateRef.current.isDragging) {
        stateRef.current.yaw += 0.0022;
        stateRef.current.arcProgress = (stateRef.current.arcProgress + 0.008) % 1;
      }

      const cx = width > 1024 ? width * 0.58 : width * 0.5;
      const cy = height * 0.52;
      const radius = Math.min(width, height) * 0.44;

      const yaw = stateRef.current.yaw;
      const pitch = stateRef.current.pitch;

      const cosY = Math.cos(yaw);
      const sinY = Math.sin(yaw);
      const cosP = Math.cos(pitch);
      const sinP = Math.sin(pitch);

      // 1. Atmosphere Radial Glow behind Globe
      const atmoGrad = ctx.createRadialGradient(cx, cy, radius * 0.82, cx, cy, radius * 1.25);
      atmoGrad.addColorStop(0, 'rgba(255, 122, 26, 0.16)');
      atmoGrad.addColorStop(0.4, 'rgba(255, 154, 77, 0.07)');
      atmoGrad.addColorStop(1, 'rgba(11, 6, 3, 0)');

      ctx.fillStyle = atmoGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.25, 0, 2 * Math.PI);
      ctx.fill();

      // Deep sphere core background
      const sphereGrad = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.1, cx, cy, radius);
      sphereGrad.addColorStop(0, '#1a0d06');
      sphereGrad.addColorStop(0.7, '#0f0804');
      sphereGrad.addColorStop(1, '#070402');

      ctx.fillStyle = sphereGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255, 154, 77, 0.25)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // 2. Project & Render 3D Dots
      const pts = globePoints.current;
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];

        // Rotate Y (yaw)
        const x1 = p.x * cosY - p.z * sinY;
        const z1 = p.x * sinY + p.z * cosY;

        // Rotate X (pitch)
        const y2 = p.y * cosP - z1 * sinP;
        const z2 = p.y * sinP + z1 * cosP;

        // Front hemisphere projection
        if (z2 > -0.05) {
          const depthAlpha = Math.max(0.1, (z2 + 0.05) / 1.05);
          const px = cx + x1 * radius;
          const py = cy + y2 * radius;

          ctx.beginPath();
          if (p.isLand) {
            ctx.arc(px, py, Math.max(1, 1.8 * depthAlpha), 0, 2 * Math.PI);
            ctx.fillStyle = `rgba(255, 154, 77, ${0.85 * depthAlpha})`;
          } else {
            ctx.arc(px, py, 0.8, 0, 2 * Math.PI);
            ctx.fillStyle = `rgba(255, 196, 140, ${0.18 * depthAlpha})`;
          }
          ctx.fill();
        }
      }

      // 3. Project Cities & Glowing Arcs
      const projectedCities: { x: number; y: number; z: number; visible: boolean; name: string }[] = [];

      GLOBAL_CITIES.forEach((c) => {
        const phi = (90 - c.lat) * (Math.PI / 180);
        const theta = (c.lon + 180) * (Math.PI / 180);

        const x0 = Math.sin(phi) * Math.cos(theta);
        const y0 = Math.cos(phi);
        const z0 = Math.sin(phi) * Math.sin(theta);

        const x1 = x0 * cosY - z0 * sinY;
        const z1 = x0 * sinY + z0 * cosY;

        const y2 = y0 * cosP - z1 * sinP;
        const z2 = y0 * sinP + z1 * cosP;

        const px = cx + x1 * radius;
        const py = cy + y2 * radius;

        projectedCities.push({
          x: px,
          y: py,
          z: z2,
          visible: z2 > 0,
          name: c.name,
        });
      });

      // Draw Arcs between city points
      FLIGHT_ARCS.forEach(([idxA, idxB]) => {
        const cA = projectedCities[idxA];
        const cB = projectedCities[idxB];

        if (cA.visible || cB.visible) {
          const mx = (cA.x + cB.x) / 2;
          const my = (cA.y + cB.y) / 2;
          const dist = Math.hypot(cB.x - cA.x, cB.y - cA.y);
          // Elevation arch
          const elevation = Math.min(70, dist * 0.3);
          const cpY = my - elevation;

          ctx.beginPath();
          ctx.moveTo(cA.x, cA.y);
          ctx.quadraticCurveTo(mx, cpY, cB.x, cB.y);
          ctx.strokeStyle = 'rgba(255, 122, 26, 0.35)';
          ctx.lineWidth = 1.2;
          ctx.stroke();

          // Traveling glowing pulse particle
          const t = stateRef.current.arcProgress;
          const px = (1 - t) * (1 - t) * cA.x + 2 * (1 - t) * t * mx + t * t * cB.x;
          const py = (1 - t) * (1 - t) * cA.y + 2 * (1 - t) * t * cpY + t * t * cB.y;

          ctx.beginPath();
          ctx.arc(px, py, 2.5, 0, 2 * Math.PI);
          ctx.fillStyle = '#fff3e8';
          ctx.shadowColor = '#ff7a1a';
          ctx.shadowBlur = 8;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      // City Node Rings & Labels
      projectedCities.forEach((c) => {
        if (c.visible) {
          ctx.beginPath();
          ctx.arc(c.x, c.y, 3, 0, 2 * Math.PI);
          ctx.fillStyle = '#ff7a1a';
          ctx.shadowColor = '#ff9a4d';
          ctx.shadowBlur = 6;
          ctx.fill();
          ctx.shadowBlur = 0;

          ctx.strokeStyle = '#fff3e8';
          ctx.lineWidth = 1;
          ctx.stroke();

          // Subtitle City Name
          ctx.font = '500 9px "Manrope", sans-serif';
          ctx.fillStyle = 'rgba(255, 243, 232, 0.7)';
          ctx.fillText(c.name, c.x + 6, c.y + 3);
        }
      });

      ctx.restore();

      if (running) {
        stateRef.current.animFrame = requestAnimationFrame(render);
      }
    };

    stateRef.current.animFrame = requestAnimationFrame(render);

    return () => {
      running = false;
      cancelAnimationFrame(stateRef.current.animFrame);
    };
  }, [isPlaying]);

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none">
      {/* 3D Canvas with drag-to-rotate */}
      <canvas
        ref={canvasRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        className="absolute inset-0 w-full h-full pointer-events-auto cursor-grab active:cursor-grabbing opacity-90 transition-opacity duration-700"
      />

      {/* Floating Pause/Spin Control Button */}
      <div className="absolute bottom-5 left-5 z-20 pointer-events-auto">
        <button
          type="button"
          onClick={() => setIsPlaying((p) => !p)}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[#120a05]/80 backdrop-blur-md border border-[rgba(255,196,140,0.25)] text-[#fff3e8] hover:border-[rgba(255,196,140,0.6)] text-xs font-medium transition-all shadow-lg hover:shadow-[0_0_15px_rgba(255,122,26,0.3)] cursor-pointer"
          title={isPlaying ? 'Pause Globe Rotation' : 'Spin Globe'}
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5 text-[#ff9a4d]" />
              <span className="text-[11px] tracking-wide">Pause Globe</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 text-[#ff7a1a]" />
              <span className="text-[11px] tracking-wide">Spin Globe</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default GlassGlobe;
