export interface User {
  id: string;
  email: string;
  name: string | null;
  is_admin?: boolean;
  email_verified?: boolean;
}

export interface ImageItem {
  id: string;
  original_filename: string | null;
  width: number | null;
  height: number | null;
  gps_lat: number | null;
  gps_lng: number | null;
  location_text: string | null;
  created_at: string | null;
  contains_faces?: boolean;
  face_count?: number;
  tags?: string[];
  categories?: string[];
}

export interface Album {
  id: string;
  name: string;
  description: string | null;
  album_type: string;
  location_text: string | null;
  gps_lat: number | null;
  gps_lng: number | null;
  start_date: string | null;
  end_date: string | null;
  is_auto_generated: boolean;
  cover_image_id: string | null;
  image_count: number;
  created_at: string;
}

export interface PersonCluster {
  id: string;
  label: string;
  faces: number;
}

export interface DashboardStats {
  total_images: number;
  total_albums: number;
  person_clusters: number;
  storage_used_mb: number;
  images_this_month: number;
  albums_this_month: number;
  most_common_location: string | null;
  unique_locations: number;
}

export interface ShareLink {
  share_id: string;
  share_url: string;
  expires_in_hours: number;
  max_views?: number;
}

