import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
}

export default function GlassCard({ children, className = "", id }: GlassCardProps) {
  return (
    <div
      id={id}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-tr from-white/5 to-white/[0.02] border border-white/10 backdrop-blur-xl shadow-2xl transform-gpu transition-all duration-300 hover:border-white/20 hover:shadow-white/[0.02] ${className}`}
    >
      {/* Visual ambient light flare */}
      <div className="absolute inset-0 bg-gradient-to-tr from-white/[0.01] to-white/[0.05] pointer-events-none" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
