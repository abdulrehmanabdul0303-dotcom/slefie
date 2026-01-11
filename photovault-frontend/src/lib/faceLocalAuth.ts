/**
 * On-Device Face Authentication (Privacy-First)
 * Face matching happens in browser, only hash sent to backend
 */

// Note: face-api.js models need to be loaded separately
// For production, models should be in public/models/ directory

export interface FaceEmbedding {
  descriptor: Float32Array;
  detection: any;
}

/**
 * Initialize face-api.js models
 * Call this once before using face detection
 */
export async function loadFaceModels(): Promise<boolean> {
  try {
    // Dynamic import to avoid SSR issues
    const faceapi = await import("face-api.js");
    
    const MODEL_URL = "/models"; // Models should be in public/models/
    
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
    ]);
    
    return true;
  } catch (error) {
    console.error("Failed to load face models:", error);
    return false;
  }
}

/**
 * Detect face and extract embedding from video element
 */
export async function detectFaceFromVideo(
  video: HTMLVideoElement
): Promise<FaceEmbedding | null> {
  try {
    const faceapi = await import("face-api.js");
    
    const detection = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceDescriptor();
    
    if (!detection) {
      return null;
    }
    
    return {
      descriptor: detection.descriptor,
      detection: detection,
    };
  } catch (error) {
    console.error("Face detection error:", error);
    return null;
  }
}

/**
 * Detect face and extract embedding from image file
 */
export async function detectFaceFromImage(
  file: File
): Promise<FaceEmbedding | null> {
  try {
    const faceapi = await import("face-api.js");
    
    const image = await faceapi.bufferToImage(file);
    
    const detection = await faceapi
      .detectSingleFace(image, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceDescriptor();
    
    if (!detection) {
      return null;
    }
    
    return {
      descriptor: detection.descriptor,
      detection: detection,
    };
  } catch (error) {
    console.error("Face detection error:", error);
    return null;
  }
}

/**
 * Calculate cosine similarity between two embeddings
 */
export function cosineSimilarity(a: Float32Array, b: Float32Array): number {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * Hash embedding for privacy (send only hash to backend)
 */
export async function hashEmbedding(embedding: Float32Array): Promise<string> {
  // Convert to array for hashing
  const array = Array.from(embedding);
  const json = JSON.stringify(array);
  
  // Use Web Crypto API for hashing
  const encoder = new TextEncoder();
  const data = encoder.encode(json);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
  
  return hashHex;
}

/**
 * Store embedding locally (IndexedDB) for privacy
 */
export async function storeEmbeddingLocally(
  userId: string,
  embedding: Float32Array
): Promise<void> {
  try {
    // Simple localStorage approach (can be upgraded to IndexedDB)
    const key = `face_embedding_${userId}`;
    const array = Array.from(embedding);
    localStorage.setItem(key, JSON.stringify(array));
  } catch (error) {
    console.error("Failed to store embedding locally:", error);
  }
}

/**
 * Retrieve embedding from local storage
 */
export async function getLocalEmbedding(userId: string): Promise<Float32Array | null> {
  try {
    const key = `face_embedding_${userId}`;
    const stored = localStorage.getItem(key);
    if (!stored) return null;
    
    const array = JSON.parse(stored);
    return new Float32Array(array);
  } catch (error) {
    console.error("Failed to retrieve embedding:", error);
    return null;
  }
}

