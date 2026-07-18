"use client";

import React, { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface ParticleSwarmProps {
  isStreaming: boolean;
}

function ParticleSwarm({ isStreaming }: ParticleSwarmProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      mouseRef.current.targetX = (event.clientX / window.innerWidth) * 2 - 1;
      mouseRef.current.targetY = -(event.clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const particleCount = 2500;
  
  // Build particle positions and neon vertex colors
  const [positions, colors] = useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    const cols = new Float32Array(particleCount * 3);
    
    const cyan = new THREE.Color("#00f2fe");
    const magenta = new THREE.Color("#f900ff");
    const violet = new THREE.Color("#7f00ff");
    const colorOptions = [cyan, magenta, violet];

    for (let i = 0; i < particleCount; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 4.5 + Math.random() * 7.5;

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);

      const col = colorOptions[Math.floor(Math.random() * colorOptions.length)];
      cols[i * 3] = col.r;
      cols[i * 3 + 1] = col.g;
      cols[i * 3 + 2] = col.b;
    }
    return [pos, cols];
  }, []);

  // GLSL Shader configurations
  const shaderConfig = useMemo(() => ({
    uniforms: {
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uStreamSpeed: { value: 1.0 }
    },
    vertexShader: `
      uniform float uTime;
      uniform vec2 uMouse;
      uniform float uStreamSpeed;
      varying vec3 vColor;
      
      void main() {
        vColor = color;
        vec3 p = position;
        
        // Fluid sine-wave wave noise pattern simulation
        float waveX = sin(p.x * 0.35 + uTime * uStreamSpeed * 1.3) * 0.75;
        float waveY = cos(p.y * 0.3 + uTime * uStreamSpeed * 1.1) * 0.55;
        float waveZ = sin(p.z * 0.4 + uTime * uStreamSpeed * 1.6) * 0.65;
        
        p.x += waveY * 0.3;
        p.y += waveZ * 0.4 + uMouse.y * 1.2;
        p.z += waveX * 0.5 + uMouse.x * 1.2;
        
        vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        
        // Size attenuation based on distance + breathe effect
        gl_PointSize = (10.0 / -mvPosition.z) * (1.0 + 0.25 * sin(uTime * 2.5));
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      
      void main() {
        // Draw smooth circular glowing neon points
        float dist = distance(gl_PointCoord, vec2(0.5));
        if (dist > 0.5) discard;
        
        float intensity = smoothstep(0.5, 0.05, dist);
        gl_FragColor = vec4(vColor, intensity * 0.8);
      }
    `
  }), []);

  useFrame((state, delta) => {
    // 1. Mouse coordinate smoothing
    mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
    mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

    // 2. Swarm rotation skewing
    if (pointsRef.current) {
      pointsRef.current.rotation.y += delta * 0.02;
      pointsRef.current.rotation.x += delta * 0.01;
      pointsRef.current.rotation.y += mouseRef.current.x * 0.003;
      pointsRef.current.rotation.x += mouseRef.current.y * 0.003;
    }

    // 3. Update GLSL uniforms
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.getElapsedTime();
      
      // Interpolate streaming uniform speed
      const targetSpeed = isStreaming ? 2.8 : 1.0;
      materialRef.current.uniforms.uStreamSpeed.value += (targetSpeed - materialRef.current.uniforms.uStreamSpeed.value) * 0.05;
      
      // Set mouse vec2
      materialRef.current.uniforms.uMouse.value.set(mouseRef.current.x, mouseRef.current.y);
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <shaderMaterial
        ref={materialRef}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        vertexColors
        {...shaderConfig}
      />
    </points>
  );
}

export default function ThreeCanvas({ isStreaming = false }: { isStreaming?: boolean }) {
  return (
    <div className="absolute inset-0 -z-10 w-full h-full pointer-events-none overflow-hidden">
      {/* Background neon visual ambient overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.18),rgba(255,255,255,0))]" />
      <div className="absolute inset-0 bg-[#02000a]" />
      
      <Canvas
        camera={{ position: [0, 0, 15], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        className="w-full h-full pointer-events-none"
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00f2fe" />
        <pointLight position={[-10, -10, -10]} intensity={1.2} color="#f900ff" />
        <ParticleSwarm isStreaming={isStreaming} />
      </Canvas>
    </div>
  );
}
