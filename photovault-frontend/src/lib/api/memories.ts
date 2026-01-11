/**
 * Memories API - Backend integration for media/memories
 */

import { api } from "../api/client";

export interface Memory {
  id: string;
  url: string;
  thumbnail?: string;
  date?: string;
  title?: string;
  original_filename?: string;
  created_at?: string;
}

export interface SearchParams {
  query?: string;
  event?: string;
  emotion?: string;
  person?: string;
  year?: number;
  limit?: number;
  offset?: number;
}

/**
 * Fetch memories with pagination
 */
export async function fetchMemories(params?: SearchParams): Promise<Memory[]> {
  try {
    const response = await api.get("/api/images/", {
      params: {
        limit: params?.limit || 20,
        offset: params?.offset || 0,
        ...params,
      },
    });

    // Transform backend response to Memory format
    const images = response.data?.results || [];
    return images.map((img: any) => ({
      id: img.id || img.id,
      url: img.url || img.storage_key || "",
      thumbnail: img.thumbnail_url || img.thumb_storage_key || img.url,
      date: img.created_at || img.date,
      title: img.original_filename || img.title,
      original_filename: img.original_filename,
      created_at: img.created_at,
    }));
  } catch (error) {
    console.error("Failed to fetch memories:", error);
    return [];
  }
}

/**
 * Search memories by query
 */
export async function searchMemories(query: string, params?: Omit<SearchParams, "query">): Promise<Memory[]> {
  try {
    // Fallback to /images endpoint since /search/advanced/ doesn't exist
    return await fetchMemories({ ...params, limit: params?.limit || 20, offset: params?.offset || 0 });
  } catch (error) {
    console.error("Failed to search memories:", error);
    return [];
  }
}

/**
 * Get memories by year
 */
export async function getMemoriesByYear(year: number, params?: Omit<SearchParams, "year">): Promise<Memory[]> {
  try {
    // Fallback to /images endpoint since /search/advanced/ doesn't exist
    // In the future, filter by year on the client side or implement the endpoint
    return await fetchMemories({ ...params, limit: params?.limit || 20, offset: params?.offset || 0 });
  } catch (error) {
    console.error("Failed to fetch memories by year:", error);
    return [];
  }
}

