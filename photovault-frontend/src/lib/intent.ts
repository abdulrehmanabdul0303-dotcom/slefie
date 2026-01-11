/**
 * Intent Parser - Converts natural language to actions
 * Simple rule-based system (placeholder for future AI integration)
 */

export type IntentType = 
  | "search_event"
  | "search_emotion"
  | "search_person"
  | "open_timeline"
  | "open_album"
  | "show_recent"
  | "unknown";

export interface Intent {
  type: IntentType;
  query?: string;
  params?: Record<string, any>;
}

/**
 * Parse natural language input to intent
 */
export function parseIntent(text: string): Intent {
  const lower = text.toLowerCase().trim();
  
  // Empty or whitespace
  if (!lower) {
    return { type: "unknown" };
  }
  
  // Event-based searches (Eid, birthday, wedding, etc.)
  const eventKeywords = ["eid", "birthday", "wedding", "party", "trip", "vacation", "holiday", "festival"];
  if (eventKeywords.some(keyword => lower.includes(keyword))) {
    return {
      type: "search_event",
      query: text,
      params: { event: extractEvent(lower) }
    };
  }
  
  // Emotion-based searches
  const emotionKeywords = {
    happy: ["happy", "joy", "smile", "laugh", "cheerful", "excited"],
    calm: ["calm", "peaceful", "serene", "quiet", "relaxed"],
    sad: ["sad", "melancholy", "nostalgic", "emotional"]
  };
  
  for (const [emotion, keywords] of Object.entries(emotionKeywords)) {
    if (keywords.some(keyword => lower.includes(keyword))) {
      return {
        type: "search_emotion",
        query: text,
        params: { emotion }
      };
    }
  }
  
  // Person-based searches
  const personKeywords = ["person", "people", "face", "friend", "family", "mom", "dad", "brother", "sister"];
  if (personKeywords.some(keyword => lower.includes(keyword))) {
    return {
      type: "search_person",
      query: text,
      params: { person: extractPerson(lower) }
    };
  }
  
  // Timeline commands
  if (lower.includes("timeline") || lower.includes("time") || lower.includes("year")) {
    return {
      type: "open_timeline",
      query: text,
      params: { year: extractYear(lower) }
    };
  }
  
  // Album commands
  if (lower.includes("album") || lower.includes("collection")) {
    return {
      type: "open_album",
      query: text,
      params: { album: extractAlbum(lower) }
    };
  }
  
  // Recent/show commands
  if (lower.includes("recent") || lower.includes("latest") || lower.includes("new") || lower.includes("dikhao") || lower.includes("show")) {
    return {
      type: "show_recent",
      query: text
    };
  }
  
  // Default: treat as general search
  return {
    type: "search_event",
    query: text,
    params: { query: text }
  };
}

/**
 * Extract event name from text
 */
function extractEvent(text: string): string {
  const events = ["eid", "birthday", "wedding", "party", "trip", "vacation"];
  for (const event of events) {
    if (text.includes(event)) {
      return event;
    }
  }
  return "unknown";
}

/**
 * Extract person name from text (simple extraction)
 */
function extractPerson(text: string): string {
  // In a real implementation, this would use NLP to extract names
  // For now, return the text after "person" or "people"
  const match = text.match(/(?:person|people|friend|family)\s+(.+)/i);
  return match ? match[1] : "unknown";
}

/**
 * Extract year from text
 */
function extractYear(text: string): number | null {
  const yearMatch = text.match(/\b(19|20)\d{2}\b/);
  return yearMatch ? parseInt(yearMatch[0]) : null;
}

/**
 * Extract album name from text
 */
function extractAlbum(text: string): string {
  const match = text.match(/(?:album|collection)\s+(.+)/i);
  return match ? match[1] : "all";
}

/**
 * Get emotion from intent (for UI reactivity)
 */
export function getEmotionFromIntent(intent: Intent): "happy" | "calm" | "sad" | "neutral" {
  if (intent.type === "search_emotion" && intent.params?.emotion) {
    return intent.params.emotion as "happy" | "calm" | "sad";
  }
  
  // Infer from query text
  const query = intent.query?.toLowerCase() || "";
  if (query.includes("happy") || query.includes("joy") || query.includes("smile")) {
    return "happy";
  }
  if (query.includes("calm") || query.includes("peace")) {
    return "calm";
  }
  if (query.includes("sad") || query.includes("nostalgic")) {
    return "sad";
  }
  
  return "neutral";
}

