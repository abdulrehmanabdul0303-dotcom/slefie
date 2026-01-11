"use client";

import { useState, useEffect, useCallback } from "react";
import { AICommandBar } from "@/components/AICommandBar";
import { MemoryGrid } from "@/components/MemoryGrid";
import { EmotionShell } from "@/components/EmotionShell";
import { TimeSlider } from "@/components/TimeSlider";
import { Intent } from "@/lib/intent";
import { fetchMemories, searchMemories, getMemoriesByYear, Memory } from "@/lib/api/memories";
import { useRouter } from "next/navigation";
import { authStore } from "@/lib/auth/auth-store";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Box, Glasses } from "lucide-react";
import { GlassCard } from "@/components/GlassCard";

/**
 * Dashboard Page - Protected Route
 * AI-First, No-Buttons Interface
 * Primary entry point for authenticated users
 */
export default function DashboardPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [currentIntent, setCurrentIntent] = useState<Intent | null>(null);
  const [currentYear, setCurrentYear] = useState<number | null>(null);
  const [offset, setOffset] = useState(0);
  const router = useRouter();

  // Check auth
  useEffect(() => {
    const token = authStore.getToken();
    if (!token) {
      router.push("/auth/login");
    }
  }, [router]);

  // Initial load
  useEffect(() => {
    loadInitialMemories();
  }, []);

  const loadInitialMemories = async () => {
    setLoading(true);
    try {
      const data = await fetchMemories({ limit: 20, offset: 0 });
      setMemories(data);
      setOffset(20);
      setHasMore(data.length === 20);
    } catch (error) {
      console.error("Failed to load memories:", error);
    }
    // Load memories by year (disabled - endpoint not implemented)
    // try {
    //   const currentYear = new Date().getFullYear();
    //   const yearData = await getMemoriesByYear(currentYear);
    //   setMemoriesByYear(yearData);
    // } catch (error) {
    //   console.error("Failed to load memories by year:", error);
    // }
    finally {
      setLoading(false);
    }
  };

  // Handle intent from AI Command Bar
  const handleIntent = useCallback(async (intent: Intent) => {
    setCurrentIntent(intent);
    setLoading(true);
    setOffset(0);

    try {
      let data: Memory[] = [];

      switch (intent.type) {
        case "search_event":
        case "search_emotion":
        case "search_person":
          // Use search endpoint
          data = await searchMemories(intent.query || "", {
            event: intent.params?.event,
            emotion: intent.params?.emotion,
            person: intent.params?.person,
            limit: 20,
          });
          break;

        case "open_timeline":
          // Load by year
          const year = intent.params?.year || new Date().getFullYear();
          setCurrentYear(year);
          data = await getMemoriesByYear(year, { limit: 20 });
          break;

        case "show_recent":
          // Show recent memories
          data = await fetchMemories({ limit: 20, offset: 0 });
          break;

        default:
          // General search
          data = await searchMemories(intent.query || "", { limit: 20 });
      }

      setMemories(data);
      setOffset(data.length);
      setHasMore(data.length === 20);
    } catch (error) {
      console.error("Failed to handle intent:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load more (infinite scroll)
  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    try {
      let data: Memory[] = [];

      if (currentYear) {
        data = await getMemoriesByYear(currentYear, { limit: 20, offset });
      } else if (currentIntent?.query) {
        data = await searchMemories(currentIntent.query, {
          limit: 20,
          offset,
          ...currentIntent.params,
        });
      } else {
        data = await fetchMemories({ limit: 20, offset });
      }

      if (data.length > 0) {
        setMemories((prev) => [...prev, ...data]);
        setOffset((prev) => prev + data.length);
        setHasMore(data.length === 20);
      } else {
        setHasMore(false);
      }
    } catch (error) {
      console.error("Failed to load more:", error);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, offset, currentYear, currentIntent]);

  // Handle year change from time slider
  const handleYearChange = useCallback(async (year: number) => {
    setCurrentYear(year);
    setCurrentIntent(null);
    setLoading(true);
    setOffset(0);

    try {
      const data = await getMemoriesByYear(year, { limit: 20 });
      setMemories(data);
      setOffset(data.length);
      setHasMore(data.length === 20);
    } catch (error) {
      console.error("Failed to load memories by year:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <EmotionShell intent={currentIntent}>
      <div className="min-h-screen pb-32">
        {/* AI Command Bar - Global, top-center */}
        <AICommandBar onIntent={handleIntent} />

        {/* Memory Grid */}
        <div className="pt-24">
          <MemoryGrid
            memories={memories}
            loading={loading}
            onLoadMore={loadMore}
            hasMore={hasMore}
          />
        </div>

        {/* Time Slider - Bottom timeline */}
        <TimeSlider
          onYearChange={handleYearChange}
          minYear={2020}
          maxYear={new Date().getFullYear()}
        />
      </div>
    </EmotionShell>
  );
}
