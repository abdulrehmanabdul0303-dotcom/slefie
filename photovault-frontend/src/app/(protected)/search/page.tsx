"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import { api } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import { toast } from "sonner";
import type { ImageItem } from "@/lib/types/models";
import { PageErrorBoundary } from "@/components/common/PageErrorBoundary";
import { SEARCH_PAGE_SIZE, SEARCH_DEBOUNCE_MS } from "@/lib/config/constants";

function debounce<T extends (...args: any[]) => void>(fn: T, ms: number) {
  let t: any;
  return (...args: any[]) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

function SearchContent({ 
  searchParams 
}: { 
  searchParams: Promise<{ q?: string }> | { q?: string } 
}) {
  const [q, setQ] = useState<string>("");
  const [location, setLocation] = useState("");
  const [hasFaces, setHasFaces] = useState<boolean | "">("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [results, setResults] = useState<ImageItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = SEARCH_PAGE_SIZE;

  const suggestionAbortRef = useRef<AbortController | null>(null);
  const searchAbortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Cancel any in-flight requests on unmount
      if (searchAbortRef.current) {
        searchAbortRef.current.abort();
      }
      if (suggestionAbortRef.current) {
        suggestionAbortRef.current.abort();
      }
    };
  }, []);

  const fetchSuggestions = useMemo(
    () =>
      debounce(async (text: string) => {
        if (!text) {
          if (mountedRef.current) {
            setSuggestions([]);
          }
          return;
        }
        
        // Cancel previous request
        if (suggestionAbortRef.current) {
          suggestionAbortRef.current.abort();
        }
        
        suggestionAbortRef.current = new AbortController();
        
        try {
          const r = await api.get(`${endpoints.searchSuggestions}?q=${encodeURIComponent(text)}`, {
            signal: suggestionAbortRef.current.signal,
          });
          
          if (!mountedRef.current) return;
          setSuggestions(r.data?.suggestions ?? r.data ?? []);
        } catch (e: any) {
          if (e.name === 'AbortError' || e.name === 'CanceledError') {
            return; // Request was cancelled, ignore
          }
          if (mountedRef.current) {
            setSuggestions([]);
          }
        }
      }, SEARCH_DEBOUNCE_MS),
    []
  );

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      // Cancel any in-flight requests on unmount
      if (searchAbortRef.current) {
        searchAbortRef.current.abort();
      }
      if (suggestionAbortRef.current) {
        suggestionAbortRef.current.abort();
      }
    };
  }, []);

  async function search(newOffset = 0) {
    // Cancel any previous search
    if (searchAbortRef.current) {
      searchAbortRef.current.abort();
    }

    searchAbortRef.current = new AbortController();
    
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      if (location) params.set("location", location);
      if (hasFaces !== "") params.set("has_faces", String(hasFaces));
      params.set("limit", String(limit));
      params.set("offset", String(newOffset));

      const r = await api.get(`${endpoints.search}?${params.toString()}`, {
        signal: searchAbortRef.current.signal,
      });
      const data = r.data;
      
      if (!mountedRef.current) return;
      setResults(data?.images ?? data ?? []);
      setTotal(data?.total ?? (data?.count ?? 0));
      setOffset(data?.offset ?? newOffset);
    } catch (e: any) {
      if (e.name === 'AbortError' || e.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      if (mountedRef.current) {
        toast.error(e?.response?.data?.detail ?? "Search failed");
      }
    }
  }

  // Initialize from URL params
  useEffect(() => {
    (async () => {
      const params = await Promise.resolve(searchParams);
      if (params?.q) {
        setQ(params.q);
      }
    })();
  }, [searchParams]);

  // Fetch suggestions when query changes
  useEffect(() => {
    fetchSuggestions(q);
  }, [q, fetchSuggestions]);

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-xl p-4 space-y-3">
        <div className="font-semibold">Advanced Search</div>

        <div className="relative">
          <input
            className="w-full border rounded-md px-3 py-2"
            placeholder="Search text..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {suggestions.length > 0 && (
            <div className="absolute z-10 mt-1 w-full bg-white border rounded-md overflow-hidden">
              {suggestions.slice(0, 8).map((s: any, idx: number) => (
                <button
                  key={idx}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                  onClick={() => {
                    setQ(String(s.value ?? s.text ?? s));
                    setSuggestions([]);
                  }}
                >
                  {String(s.value ?? s.text ?? s)}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          <input 
            className="border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]" 
            placeholder="Location" 
            value={location} 
            onChange={(e) => setLocation(e.target.value)} 
          />
          <input 
            type="date" 
            className="border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]" 
            value={startDate} 
            onChange={(e) => setStartDate(e.target.value)} 
          />
          <input 
            type="date" 
            className="border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]" 
            value={endDate} 
            onChange={(e) => setEndDate(e.target.value)} 
          />
          <select 
            className="border rounded-md px-3 py-2.5 text-base sm:text-sm min-h-[44px]" 
            value={String(hasFaces)} 
            onChange={(e) => setHasFaces(e.target.value === "" ? "" : e.target.value === "true")}
          >
            <option value="">Has faces?</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
          <button 
            className="bg-black text-white rounded-md px-3 py-2.5 text-sm min-h-[44px] col-span-1 sm:col-span-2 lg:col-span-1" 
            onClick={() => search(0)}
          >
            Search
          </button>
        </div>

        <div className="flex gap-2">
          <button
            className="border rounded-md px-3 py-2.5 text-sm min-h-[44px]"
            onClick={() => {
              setQ(""); setLocation(""); setHasFaces(""); setStartDate(""); setEndDate("");
              setSuggestions([]); setResults([]); setTotal(0); setOffset(0);
            }}
            aria-label="Clear search filters"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="text-sm text-gray-600">
        Showing {results.length} of {total}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3">
        {results.map((img) => (
          <a 
            key={img.id} 
            href={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageView(img.id)}`} 
            target="_blank" 
            className="bg-white border rounded-xl overflow-hidden hover:shadow-sm transition"
          >
            <img 
              src={`${process.env.NEXT_PUBLIC_API_BASE_URL}${endpoints.imageThumb(img.id)}`} 
              className="w-full h-40 sm:h-48 object-cover" 
              alt="res" 
            />
            <div className="p-2 sm:p-3 text-xs sm:text-sm truncate">{img.original_filename ?? "Untitled"}</div>
          </a>
        ))}
      </div>

      <div className="flex gap-2">
        <button 
          className="flex-1 sm:flex-none border rounded-md px-3 py-2.5 text-sm min-h-[44px] disabled:opacity-50" 
          disabled={offset <= 0} 
          onClick={() => search(Math.max(0, offset - limit))}
          aria-label="Previous page"
        >
          Prev
        </button>
        <button 
          className="flex-1 sm:flex-none border rounded-md px-3 py-2.5 text-sm min-h-[44px] disabled:opacity-50" 
          disabled={offset + limit >= total} 
          onClick={() => search(offset + limit)}
          aria-label="Next page"
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default function SearchPage({ 
  searchParams 
}: { 
  searchParams: Promise<{ q?: string }> | { q?: string } 
}) {
  return (
    <PageErrorBoundary pageName="Search">
      <SearchContent searchParams={searchParams} />
    </PageErrorBoundary>
  );
}
