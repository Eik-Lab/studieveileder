"use client";

import { useState, useRef, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Bot, User, AlertCircle } from "lucide-react";
import { apiClient, isTimeoutError } from "@/lib/api-client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

const suggestedQuestions = [
  "Hvordan søker jeg om permisjon?",
  "Når er fristen for semesterregistrering?",
  "Hvor finner jeg timeplan?",
  "Hva er kravene for bacheloroppgave?",
];

export default function Advisor() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hei! Jeg er NMBU sin studieveileder. Hvordan kan jeg hjelpe deg i dag?",
      timestamp: Date.now(),
    },
  ]);

  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    setShowSuggestions(false);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const data = await apiClient.post<{ answer: string }>(
        "/api/chat",
        { query: content },
        { timeout: 45000 }
      );

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "Beklager, ingen svar tilgjengelig.",
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: isTimeoutError(err)
          ? "Forespørselen tok for lang tid. Prøv igjen."
          : "Kunne ikke koble til backend.",
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const formatTime = (timestamp: number) =>
    new Date(timestamp).toLocaleTimeString("no-NO", {
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F6F2]">

      <Header />

      <main className="flex-1 pt-12 pb-24">

        <div className="container mx-auto px-4 max-w-6xl">

          {/* Mobile warning */}
          <div className="lg:hidden mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />

            <div>
              <h3 className="font-semibold text-amber-900 mb-1">
                Under utvikling
              </h3>

              <p className="text-sm text-amber-800">
                Kontakt:{" "}
                <a
                  href="mailto:studieveiledning@nmbu.no"
                  className="underline"
                >
                  studieveiledning@nmbu.no
                </a>
              </p>
            </div>
          </div>

          <Card
            className="
              flex
              flex-col
              overflow-hidden
              shadow-2xl
              border
              border-[#D6E6E2]
              bg-[#F7F6F2]
            "
            style={{ minHeight: "calc(100vh - 180px)" }}
          >

            {/* Header */}
            <CardHeader className="bg-[#F7F6F2] border-b border-[#D6E6E2]">

              <CardTitle className="text-3xl md:text-4xl text-[#1F3F3A]">
                Digital studieveileder
              </CardTitle>

              <CardDescription className="text-[#5C6F6B]">
                Spør om studier, eksamen og campus
              </CardDescription>

            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-0">

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5 scroll-smooth">

                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >

                    {message.role === "assistant" && (
                      <div className="w-10 h-10 rounded-full bg-[#3B7C72] flex items-center justify-center">
                        <Bot className="w-5 h-5 text-white" />
                      </div>
                    )}

                    <div
                      className={`
                        max-w-[70%]
                        rounded-xl
                        px-4
                        py-3
                        border
                        ${
                          message.role === "user"
                            ? "bg-[#5BA89C]/20 border-[#5BA89C] text-[#14302B]"
                            : "bg-white border-[#D6E6E2] text-[#1F3F3A]"
                        }
                      `}
                    >
                      <p className="text-sm md:text-base whitespace-pre-line">
                        {message.content}
                      </p>

                      <span className="text-xs opacity-60 block mt-1">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>

                    {message.role === "user" && (
                      <div className="w-10 h-10 rounded-full bg-[#5BA89C] flex items-center justify-center">
                        <User className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </div>
                ))}

                {/* Typing */}
                {isTyping && (
                  <div className="flex gap-3 justify-start">

                    <div className="w-10 h-10 rounded-full bg-[#3B7C72] flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>

                    <div className="bg-white border border-[#D6E6E2] rounded-xl px-4 py-3">

                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-[#3B7C72] rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-[#3B7C72] rounded-full animate-bounce delay-150" />
                        <div className="w-2 h-2 bg-[#3B7C72] rounded-full animate-bounce delay-300" />
                      </div>

                    </div>
                  </div>
                )}

                {/* Suggestions */}
                {showSuggestions && messages.length === 1 && (
                  <div className="space-y-2 pt-2">

                    <p className="text-sm text-[#5C6F6B]">
                      Foreslåtte spørsmål:
                    </p>

                    <div className="flex flex-wrap gap-2">

                      {suggestedQuestions.map((q) => (
                        <Button
                          key={q}
                          variant="outline"
                          size="sm"
                          onClick={() => handleSendMessage(q)}
                          className="border-[#5BA89C] text-[#1F3F3A] hover:bg-[#5BA89C]/10"
                        >
                          {q}
                        </Button>
                      ))}

                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />

              </div>

              {/* Input */}
              <div className="border-t border-[#D6E6E2] bg-white p-4">

                <div className="flex gap-2">

                  <Input
                    placeholder="Skriv ditt spørsmål..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="border-[#5BA89C] focus:ring-[#5BA89C]"
                  />

                  <Button
                    onClick={() => handleSendMessage(inputValue)}
                    disabled={!inputValue.trim()}
                    className="bg-[#3B7C72] hover:bg-[#2F655D]"
                  >
                    Send
                  </Button>

                </div>

              </div>

            </CardContent>
          </Card>

        </div>
      </main>

      <Footer />

    </div>
  );
}
