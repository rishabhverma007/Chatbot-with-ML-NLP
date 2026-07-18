"use client";

import React, { useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import ThreeCanvas from "../components/ThreeCanvas";
import ToggleButton from "../components/ToggleButton";
import ChatWindow from "../components/ChatWindow";
import GlassCard from "../components/GlassCard";
import { Shield, Sparkles, Terminal } from "lucide-react";

export default function Home() {
  const [mode, setMode] = useState<"chitchat" | "knowledge_query">("knowledge_query");
  
  // Custom WebSocket connection hook pointing to backend uvicorn host
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/chat";
  const {
    messages,
    isConnected,
    activeNode,
    nodeLogs,
    status,
    sendMessage,
    clearHistory
  } = useWebSocket(wsUrl);

  const handleSendMessage = (text: string) => {
    sendMessage(text, mode);
  };

  return (
    <main className="relative min-h-screen flex flex-col justify-center items-center px-4 py-8 overflow-x-hidden overflow-y-auto">
      
      {/* 3D Particle Orbit Backdrop */}
      <ThreeCanvas isStreaming={status === "streaming"} />

      {/* Decorative background glows */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Top Header Card */}
      <div className="w-full max-w-4xl mb-6 relative z-10">
        <GlassCard className="py-4 px-6 border-white/5 bg-black/10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-r from-blue-500/20 to-purple-600/20 p-2 rounded-xl border border-blue-500/20">
                <Terminal className="text-blue-400 animate-pulse" size={20} />
              </div>
              <div>
                <h1 className="text-xl font-black tracking-widest text-white flex items-center gap-2">
                  AETHERIS CORE <Sparkles size={14} className="text-purple-400" />
                </h1>
                <p className="text-[10px] uppercase font-mono text-white/50 tracking-wider">
                  Agentic Cognitive RAG Workspace
                </p>
              </div>
            </div>

            {/* Mode Switcher pill */}
            <ToggleButton mode={mode} onChange={setMode} />

            {/* Status indicators */}
            <div className="flex items-center gap-2.5 bg-black/30 border border-white/5 px-4 py-2 rounded-full">
              <Shield size={12} className="text-emerald-400" />
              <span className="text-[10px] font-mono text-white/70 uppercase tracking-widest">
                Nodes Secured
              </span>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Main Interactive Chat Window */}
      <div className="w-full max-w-4xl relative z-10">
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          activeNode={activeNode}
          nodeLogs={nodeLogs}
          status={status}
          isConnected={isConnected}
          onClearHistory={clearHistory}
          currentMode={mode}
        />
      </div>

      {/* Footer System Credits */}
      <div className="mt-6 text-[10px] font-mono text-white/35 uppercase tracking-widest z-10 flex items-center gap-2">
        <span>Aetheris Platform v1.0.0</span>
        <span>•</span>
        <span>Agent Core Online</span>
      </div>
    </main>
  );
}
