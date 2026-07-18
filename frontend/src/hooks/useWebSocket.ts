"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface Entity {
  entity: string;
  label: string;
  start: number;
  end: number;
}

export interface Document {
  id: string;
  title: string;
  content: string;
}

export interface AgentTrace {
  node: string;
  status: "running" | "completed" | "streaming";
  message: string;
  data?: any;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  mode?: "chitchat" | "knowledge_query";
  traces?: AgentTrace[];
  retrievedDocs?: Document[];
  entities?: Entity[];
}

export function useWebSocket(
  url: string = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/chat"
) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [currentAssistantResponse, setCurrentAssistantResponse] = useState<string>("");
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [nodeLogs, setNodeLogs] = useState<AgentTrace[]>([]);
  const [status, setStatus] = useState<"idle" | "thinking" | "streaming">("idle");

  const socketRef = useRef<WebSocket | null>(null);
  const traceAccumulatorRef = useRef<AgentTrace[]>([]);
  const responseAccumulatorRef = useRef<string>("");
  const currentMsgIdRef = useRef<string | null>(null);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      if (socketRef.current?.readyState === WebSocket.OPEN) return;

      setIsConnecting(true);
      socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        console.log("WebSocket connected to backend.");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "token") {
            // Streaming tokens
            setStatus("streaming");
            setActiveNode(data.step || "generating");
            
            responseAccumulatorRef.current += data.content;
            setCurrentAssistantResponse(responseAccumulatorRef.current);

            // Update messages state dynamically for real-time visual growth
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === currentMsgIdRef.current
                  ? { ...msg, content: responseAccumulatorRef.current }
                  : msg
              )
            );
          } else if (data.type === "status") {
            const log: AgentTrace = {
              node: data.step,
              status: data.step === "completed" ? "completed" : "running",
              message: data.message || "",
              data: data.data
            };

            if (data.step !== "completed") {
              traceAccumulatorRef.current.push(log);
              setNodeLogs([...traceAccumulatorRef.current]);
              setStatus("thinking");
              setActiveNode(data.step);
            } else {
              setActiveNode(null);
              setStatus("idle");
              
              if (currentMsgIdRef.current) {
                const state = data.state;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === currentMsgIdRef.current
                      ? {
                          ...msg,
                          retrievedDocs: state?.retrieved_docs,
                          entities: state?.entities,
                          traces: [...traceAccumulatorRef.current]
                        }
                      : msg
                  )
                );
              }
              
              responseAccumulatorRef.current = "";
              traceAccumulatorRef.current = [];
              currentMsgIdRef.current = null;
            }
          } else if (data.type === "error") {
            console.error("Backend error received:", data.content);
            setStatus("idle");
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        setStatus("idle");
        console.log("WebSocket disconnected.");
        reconnectTimeout = setTimeout(connect, 3000);
      };

      socket.onerror = (err) => {
        console.error("WebSocket error occurred:", err);
        socket?.close();
      };
    };

    connect();

    return () => {
      if (socket) {
        socket.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [url]);

  const sendMessage = useCallback((text: string, mode: "chitchat" | "knowledge_query") => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.warn("Cannot send message: WebSocket is not open.");
      return;
    }

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;
    currentMsgIdRef.current = assistantMsgId;
    responseAccumulatorRef.current = "";
    traceAccumulatorRef.current = [];

    // Reset temporary states
    setCurrentAssistantResponse("");
    setNodeLogs([]);
    setStatus("thinking");

    // Add user message and pending assistant slot
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: text, mode },
      { id: assistantMsgId, role: "assistant", content: "", mode }
    ]);

    // Send payload
    socketRef.current.send(JSON.stringify({ message: text, mode }));
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setCurrentAssistantResponse("");
    setNodeLogs([]);
    setStatus("idle");
  }, []);

  return {
    messages,
    isConnected,
    isConnecting,
    currentAssistantResponse,
    activeNode,
    nodeLogs,
    status,
    sendMessage,
    clearHistory
  };
}
export default useWebSocket;
