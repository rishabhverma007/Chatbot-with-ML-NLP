"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Cpu, ChevronRight, Activity, Trash2 } from "lucide-react";
import { ChatMessage, AgentTrace } from "../hooks/useWebSocket";
import GlassCard from "./GlassCard";

interface ChatWindowProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  activeNode: string | null;
  nodeLogs: AgentTrace[];
  status: "idle" | "thinking" | "streaming";
  isConnected: boolean;
  onClearHistory: () => void;
  currentMode: "chitchat" | "knowledge_query";
}

export default function ChatWindow({
  messages,
  onSendMessage,
  activeNode,
  nodeLogs,
  status,
  isConnected,
  onClearHistory,
  currentMode
}: ChatWindowProps) {
  const [inputValue, setInputValue] = useState("");
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive or tokens stream
  useEffect(() => {
    if (scrollRef.current) {
      const isStreaming = status === "streaming";
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: isStreaming ? "auto" : "smooth"
      });
    }
  }, [messages, nodeLogs, status]);

  // Adjust textarea height based on content size
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    onSendMessage(inputValue.trim());
    setInputValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const toggleTraceExpansion = (msgId: string) => {
    setExpandedTraceId(expandedTraceId === msgId ? null : msgId);
  };

  return (
    <GlassCard className="flex flex-col h-[70vh] w-full max-w-4xl mx-auto rounded-3xl overflow-hidden shadow-2xl p-0 relative bg-black/40 border-white/10">
      
      {/* Upper header block */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/20">
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse" : "bg-red-500"}`} />
          <h2 className="text-sm font-bold tracking-wider uppercase text-white/90">
            System Control Terminal
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] bg-white/5 border border-white/10 text-white/60 px-2.5 py-1 rounded-full font-mono">
            Mode: {currentMode === "chitchat" ? "Casual Chat" : "RAG Engine"}
          </span>
          <button
            onClick={onClearHistory}
            className="text-white/40 hover:text-red-400 hover:bg-red-500/10 p-1.5 rounded-full transition-all duration-300 cursor-pointer"
            title="Clear Chat History"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* Messages area container */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar space-y-6"
      >
        <AnimatePresence initial={false}>
          {messages.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="h-full flex flex-col items-center justify-center text-center p-8 opacity-60"
            >
              <Cpu size={48} className="text-blue-400/60 mb-4 animate-pulse" />
              <p className="text-white/80 font-medium max-w-sm">
                System online. Select a mode above and send a message to trigger agentic workflow.
              </p>
              <div className="mt-4 text-xs font-mono text-white/40 bg-white/5 px-3 py-1.5 rounded border border-white/5">
                Query: &quot;Explain RAG&quot; or &quot;FastAPI WebSockets&quot;
              </div>
            </motion.div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === "user";
              const showTrace = msg.traces && msg.traces.length > 0;
              const isExpanded = expandedTraceId === msg.id;

              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                >
                  <div className="max-w-[85%] relative group">
                    {/* User speech bubbles */}
                    {isUser ? (
                      <div className="bg-gradient-to-r from-blue-600/35 to-indigo-600/35 border border-blue-500/20 text-white/95 rounded-2xl px-5 py-3.5 shadow-md">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    ) : (
                      /* Assistant speech bubbles (Glass Card styling) */
                      <div className="rounded-2xl border border-white/10 bg-white/[0.02] text-white/95 px-5 py-3.5 shadow-md backdrop-blur-md">
                        {msg.content === "" ? (
                          <div className="flex items-center gap-2 py-1.5 opacity-60">
                            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                          </div>
                        ) : (
                          <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                            {msg.content}
                          </div>
                        )}

                        {/* Extra metadata tabs for RAG outputs */}
                        {!isUser && msg.content !== "" && (
                          <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap gap-2 items-center justify-between text-xs">
                            <div className="flex gap-2">
                              {msg.entities && msg.entities.length > 0 && (
                                <span className="bg-blue-500/10 text-blue-300/80 px-2 py-0.5 rounded border border-blue-500/10">
                                  {msg.entities.length} Entities
                                </span>
                              )}
                              {msg.retrievedDocs && msg.retrievedDocs.length > 0 && (
                                <span className="bg-purple-500/10 text-purple-300/80 px-2 py-0.5 rounded border border-purple-500/10">
                                  {msg.retrievedDocs.length} Sources
                                </span>
                              )}
                            </div>
                            
                            {showTrace && (
                              <button
                                onClick={() => toggleTraceExpansion(msg.id)}
                                className="flex items-center gap-1 text-white/40 hover:text-white transition-all duration-300 cursor-pointer"
                              >
                                {isExpanded ? "Hide Logs" : "Trace RAG Logs"}
                                <ChevronRight size={13} className={`transform transition-transform ${isExpanded ? "rotate-90" : ""}`} />
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Expanded Trace / Debug Log view */}
                  {!isUser && showTrace && isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-3 w-full bg-black/35 rounded-xl border border-white/5 p-4 text-[11px] font-mono text-white/60 space-y-2.5 overflow-hidden"
                    >
                      <h4 className="text-white/80 font-bold tracking-widest text-[9px] uppercase border-b border-white/5 pb-1">
                        Agent State Transition Trace Logs
                      </h4>
                      {msg.traces?.map((trace, i) => (
                        <div key={i} className="flex gap-2.5 items-start">
                          <span className="text-blue-400">[{trace.node}]</span>
                          <div className="flex-1">
                            <p className="text-white/85">{trace.message}</p>
                            {trace.data && (
                              <pre className="mt-1 bg-white/[0.02] p-1.5 rounded text-[10px] overflow-x-auto text-blue-300">
                                {JSON.stringify(trace.data, null, 2)}
                              </pre>
                            )}
                          </div>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </motion.div>
              );
            })
          )}
        </AnimatePresence>

        {/* Real-time State Machine pipeline visualizer display */}
        {status !== "idle" && nodeLogs.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 rounded-2xl bg-white/[0.01] border border-white/5 space-y-3.5"
          >
            <div className="flex items-center gap-2 text-xs font-semibold text-white/70 uppercase tracking-widest">
              <Activity size={12} className="text-blue-400 animate-pulse" />
              <span>Pipeline Stage Pipeline</span>
            </div>
            
            {/* Horizontal timeline chart of node states */}
            <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
              {[
                { id: "ner_extracted", label: "NER Extractor" },
                { id: "intent_routed", label: "Intent Router" },
                { id: "retrieving", label: "Chroma Search" },
                { id: "vector_searched", label: "Vector Search" },
                { id: "reranked", label: "Cross Rerank" },
                { id: "generating", label: "Gemini Stream" }
              ].map((step) => {
                const log = nodeLogs.find((l) => l.node === step.id);
                const isActive = activeNode === step.id;
                const isCompleted = log && log.status === "completed";
                const isStreaming = log && log.status === "streaming";

                let borderStyle = "border-white/5";
                let textStyle = "text-white/30";
                let glowStyle = "";

                if (isActive || isStreaming) {
                  borderStyle = "border-blue-500/50 bg-blue-500/10";
                  textStyle = "text-blue-200 font-bold";
                  glowStyle = "shadow-[0_0_12px_rgba(59,130,246,0.4)] animate-pulse scale-[1.02] border-blue-400/80";
                } else if (isCompleted) {
                  borderStyle = "border-emerald-500/50 bg-emerald-500/5";
                  textStyle = "text-emerald-300";
                }

                return (
                  <div
                    key={step.id}
                    className={`flex flex-col items-center justify-center p-2 rounded-lg border text-center transition-all duration-300 ${borderStyle} ${glowStyle}`}
                  >
                    <span className={`text-[10px] leading-tight truncate w-full ${textStyle}`}>{step.label}</span>
                    <span className="text-[9px] font-mono opacity-50 mt-1 uppercase">
                      {isActive || isStreaming ? "Active" : isCompleted ? "Done" : "Pending"}
                    </span>
                  </div>
                );
              })}
            </div>
            
            {/* Live trace feed */}
            <div className="text-[11px] font-mono text-white/50 bg-black/20 p-2.5 rounded border border-white/5 flex gap-2 items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
              <span>{nodeLogs[nodeLogs.length - 1]?.message}</span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input container footer */}
      <form 
        onSubmit={handleSend}
        className="px-6 py-4 border-t border-white/5 bg-black/40 flex gap-3 items-center"
      >
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder={`Send prompt to system (${currentMode === "chitchat" ? "casual chatter" : "RAG query searching"})...`}
          disabled={status !== "idle"}
          className="flex-1 rounded-2xl px-5 py-3.5 text-sm text-white glass-input text-white/90 placeholder-white/30 disabled:opacity-40 resize-none max-h-[120px] custom-scrollbar overflow-y-auto"
        />
        <button
          type="submit"
          disabled={status !== "idle" || !inputValue.trim()}
          className="bg-blue-600 hover:bg-blue-500 hover:scale-105 active:scale-95 text-white rounded-full p-3.5 transition-all duration-300 disabled:opacity-40 disabled:scale-100 disabled:hover:bg-blue-600 flex items-center justify-center shadow-lg hover:shadow-blue-500/40 border border-blue-400/20 cursor-pointer"
        >
          <Send size={16} />
        </button>
      </form>
    </GlassCard>
  );
}
