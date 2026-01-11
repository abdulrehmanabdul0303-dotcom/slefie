'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  Eye, 
  Clock, 
  Download, 
  Lock, 
  Unlock,
  Image as ImageIcon,
  User,
  Calendar,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import Image from 'next/image';

interface ClientPageProps {
  params: {
    token: string;
  };
}

interface LinkMeta {
  valid: boolean;
  error?: string;
  album_name?: string;
  creator_name?: string;
  photo_count?: number;
  expires_at?: string;
  time_remaining?: string;
  views_remaining?: string;
  download_enabled?: boolean;
  watermark_enabled?: boolean;
  branding?: {
    title: string;
    subtitle: string;
    protected_by: string;
  };
}

interface AlbumContent {
  album: {
    name: string;
    description: string;
    image_count: number;
    images: Array<{
      id: number;
      filename: string;
      thumbnail_url: string;
      preview_url: string;
      download_url?: string;
      metadata: {
        size: number;
        dimensions?: string;
        date_taken?: string;
      };
    }>;
  };
  share_info: {
    expires_at: string;
    time_remaining: string;
    views_remaining: string;
    download_enabled: boolean;
    watermark_enabled: boolean;
  };
}

export default function ClientPage({ params }: ClientPageProps) {
  const [meta, setMeta] = useState<LinkMeta | null>(null);
  const [content, setContent] = useState<AlbumContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [passcode, setPasscode] = useState('');
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [selectedImage, setSelectedImage] = useState<number | null>(null);

  useEffect(() => {
    fetchLinkMeta();
  }, [params.token]);

  const fetchLinkMeta = async () => {
    try {
      const response = await fetch(`/api/shares/client/${params.token}/meta/`);
      const data = await response.json();

      if (data.success) {
        setMeta(data.meta);
      } else {
        setMeta({ valid: false, error: data.error?.code || 'UNKNOWN_ERROR' });
      }
    } catch (error) {
      setMeta({ valid: false, error: 'NETWORK_ERROR' });
    } finally {
      setIsLoading(false);
    }
  };

  const unlockContent = async () => {
    setIsUnlocking(true);
    
    try {
      const response = await fetch(`/api/shares/client/${params.token}/access/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          passcode: passcode,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setContent(data.content);
        setIsUnlocked(true);
        toast.success('Album unlocked successfully!');
      } else {
        toast.error(data.error?.message || 'Failed to unlock album');
      }
    } catch (error) {
      toast.error('Failed to unlock album');
    } finally {
      setIsUnlocking(false);
    }
  };

  const downloadImage = (imageUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Error states
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading your photos...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!meta?.valid) {
    const errorMessages = {
      EXPIRED: 'This link has expired',
      LIMIT_REACHED: 'View limit has been reached',
      REVOKED: 'This link has been revoked',
      NOT_FOUND: 'Link not found',
      NETWORK_ERROR: 'Network error occurred',
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p className="text-muted-foreground mb-4">
              {errorMessages[meta.error as keyof typeof errorMessages] || 'Unknown error occurred'}
            </p>
            <Badge variant="destructive">{meta.error}</Badge>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Landing page (before unlock)
  if (!isUnlocked) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="font-semibold">PhotoVault</h1>
                  <p className="text-sm text-muted-foreground">Secure Photo Delivery</p>
                </div>
              </div>
              <Badge variant="outline" className="flex items-center gap-1">
                <Shield className="h-3 w-3" />
                {meta.branding?.protected_by}
              </Badge>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-2xl mx-auto px-4 py-12">
          <Card className="shadow-lg">
            <CardHeader className="text-center pb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ImageIcon className="h-8 w-8 text-blue-600" />
              </div>
              <CardTitle className="text-2xl">{meta.branding?.title}</CardTitle>
              <CardDescription className="text-lg">
                {meta.branding?.subtitle}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* Album Info */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                    <User className="h-3 w-3" />
                    Photographer
                  </div>
                  <div className="font-semibold">{meta.creator_name}</div>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                    <ImageIcon className="h-3 w-3" />
                    Photos
                  </div>
                  <div className="font-semibold">{meta.photo_count}</div>
                </div>
              </div>

              {/* Security Info */}
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium">Secure Access</span>
                  </div>
                  <Badge variant="outline">Encrypted</Badge>
                </div>

                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">Expires</span>
                  </div>
                  <span className="text-sm font-semibold">{meta.time_remaining}</span>
                </div>

                {meta.download_enabled && (
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Download className="h-4 w-4 text-purple-600" />
                      <span className="text-sm font-medium">Downloads</span>
                    </div>
                    <Badge variant="outline">Enabled</Badge>
                  </div>
                )}

                {meta.watermark_enabled && (
                  <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-orange-600" />
                      <span className="text-sm font-medium">Watermarked</span>
                    </div>
                    <Badge variant="outline">Protected</Badge>
                  </div>
                )}
              </div>

              {/* Passcode Input (if required) */}
              <div className="space-y-3">
                <Label htmlFor="passcode">Enter Passcode (if provided)</Label>
                <Input
                  id="passcode"
                  type="password"
                  placeholder="Optional passcode"
                  value={passcode}
                  onChange={(e) => setPasscode(e.target.value)}
                />
              </div>

              {/* Unlock Button */}
              <Button
                onClick={unlockContent}
                disabled={isUnlocking}
                className="w-full"
                size="lg"
              >
                {isUnlocking ? (
                  <>
                    <Lock className="h-4 w-4 mr-2 animate-spin" />
                    Unlocking...
                  </>
                ) : (
                  <>
                    <Unlock className="h-4 w-4 mr-2" />
                    View Photos
                  </>
                )}
              </Button>

              {/* Footer */}
              <div className="text-center text-sm text-muted-foreground pt-4 border-t">
                <p>Powered by PhotoVault • Secure Photo Delivery</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Album content (after unlock)
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold">{content?.album.name}</h1>
              <p className="text-sm text-muted-foreground">
                {content?.album.image_count} photos • {content?.share_info.time_remaining} remaining
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                {content?.share_info.views_remaining} views left
              </Badge>
              {content?.share_info.download_enabled && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Download className="h-3 w-3" />
                  Downloads enabled
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Photo Grid */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {content?.album.images.map((image) => (
            <Card key={image.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <div className="aspect-square relative">
                <Image
                  src={image.thumbnail_url}
                  alt={image.filename}
                  fill
                  className="object-cover cursor-pointer"
                  onClick={() => setSelectedImage(image.id)}
                />
              </div>
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium truncate">{image.filename}</p>
                  {content?.share_info.download_enabled && image.download_url && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => downloadImage(image.download_url!, image.filename)}
                    >
                      <Download className="h-3 w-3" />
                    </Button>
                  )}
                </div>
                {image.metadata.dimensions && (
                  <p className="text-xs text-muted-foreground">
                    {image.metadata.dimensions}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 pt-8 border-t">
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Shield className="h-4 w-4" />
            <span>Secured by PhotoVault</span>
          </div>
        </div>
      </div>
    </div>
  );
}