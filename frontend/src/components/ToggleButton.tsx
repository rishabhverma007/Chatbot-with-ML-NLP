"use client";

import React from "react";
import { motion } from "framer-motion";
import { MessageSquare, Database } from "lucide-react";

interface ToggleButtonProps {
  mode: "chitchat" | "knowledge_query";
  onChange: (mode: "chitchat" | "knowledge_query") => void;
}

export default function ToggleButton({ mode, onChange }: ToggleButtonProps) {
  return (
    <div className="relative flex p-1.5 rounded-full bg-black/40 border border-white/5 backdrop-blur-md w-fit mx-auto select-none shadow-lg">
      
      {/* Dynamic selection background slider */}
      <div className="absolute inset-1.5 flex justify-start pointer-events-none">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500/20 to-purple-600/20 border border-blue-500/20 rounded-full shadow-inner shadow-blue-500/5"
          initial={false}
          animate={{
            x: mode === "chitchat" ? 0 : 156,
            width: mode === "chitchat" ? 144 : 196
          }}
          transition={{ type: "spring", stiffness: 350, damping: 30 }}
        />
      </div>

      {/* Casual Chitchat Mode */}
      <button
        onClick={() => onChange("chitchat")}
        className={`relative z-10 flex items-center justify-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wider uppercase transition-colors duration-300 w-36 ${
          mode === "chitchat" ? "text-blue-300" : "text-gray-400 hover:text-white"
        }`}
      >
        <MessageSquare size={13} className="opacity-85" />
        Chitchat
      </button>

      {/* RAG Agentic Search Mode */}
      <button
        onClick={() => onChange("knowledge_query")}
        className={`relative z-10 flex items-center justify-center gap-2 px-5 py-2 rounded-full text-xs font-semibold tracking-wider uppercase transition-colors duration-300 w-48 ${
          mode === "knowledge_query" ? "text-purple-300" : "text-gray-400 hover:text-white"
        }`}
      >
        <Database size={13} className="opacity-85" />
        Agentic RAG
      </button>
    </div>
  );
}
