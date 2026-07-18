import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "../styles/globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Aetheris 3D | Next-Gen Agentic RAG Platform",
  description: "An immersive 3D Glassmorphic AI Chatbot platform built with FastAPI, WebSockets, React Three Fiber, and a LangGraph ReAct intent router loop.",
  keywords: "FastAPI, NextJS, React Three Fiber, Glassmorphism, Agentic RAG, NLP routing, WebSockets, Three.js",
  authors: [{ name: "Antigravity Team" }]
};

export default function RootLayout({
  children,
  }: Readonly<{
    children: React.ReactNode;
  }>) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="antialiased min-h-screen bg-[#030014]">
        {children}
      </body>
    </html>
  );
}
