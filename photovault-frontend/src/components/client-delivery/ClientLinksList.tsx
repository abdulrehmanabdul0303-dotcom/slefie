'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Copy, 
  Eye, 
  Clock, 
  Download, 
  Shield, 
  Trash2, 
  ExternalLink,
  MoreHorizontal,
  QrCode
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

interface ClientLink {
  id: number;
  album_name: string;
  album_id: number;
  created_at: string;
  expires_at: string;
  is_expired: boolean;
  is_valid: boolean;
  view_count: number;
  max_views: number;
  views_remaining: string;
  time_remaining: string;
  download_enabled: boolean;
  watermark_enabled: boolean;
  last_accessed: string | null;
  client_url: string;
}

export function ClientLinksList() {
  const [links, setLinks] = useState<ClientLink[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchClientLinks();
  }, []);

  const fetchClientLinks = async () => {
    try {
      const response = await fetch('/api/shares/client/list/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      const data = await response.json();

      if (data.success) {
        setLinks(data.links);
      } else {
        toast.error('Failed to fetch client links');
      }
    } catch (error) {
      toast.error('Failed to fetch client links');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Link copied to clipboard!');
  };

  const revokeLink = async (linkId: number) => {
    try {
      const response = await fetch(`/api/shares/client/${linkId}/revoke/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      const data = await response.json();

      if (data.success) {
        toast.success('Link revoked successfully');
        fetchClientLinks(); // Refresh the list
      } else {
        toast.error('Failed to revoke link');
      }
    } catch (error) {
      toast.error('Failed to revoke link');
    }
  };

  const getStatusBadge = (link: ClientLink) => {
    if (!link.is_valid) {
      if (link.is_expired) {
        return <Badge variant="destructive">Expired</Badge>;
      }
      return <Badge variant="secondary">Revoked</Badge>;
    }
    
    if (link.max_views > 0 && link.view_count >= link.max_views) {
      return <Badge variant="destructive">Limit Reached</Badge>;
    }
    
    return <Badge variant="default">Active</Badge>;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (links.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-muted-foreground">
            <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No Client Links Yet</h3>
            <p>Create your first professional client delivery link to get started.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Client Delivery Links</h2>
        <Badge variant="outline">{links.length} Total Links</Badge>
      </div>

      <div className="space-y-4">
        {links.map((link) => (
          <Card key={link.id} className={!link.is_valid ? 'opacity-60' : ''}>
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{link.album_name}</CardTitle>
                  <CardDescription>
                    Created {formatDistanceToNow(new Date(link.created_at), { addSuffix: true })}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(link)}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => copyToClipboard(link.client_url)}>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy Link
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <QrCode className="h-4 w-4 mr-2" />
                        Show QR Code
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Preview
                      </DropdownMenuItem>
                      {link.is_valid && (
                        <DropdownMenuItem 
                          onClick={() => revokeLink(link.id)}
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Revoke Link
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Link URL */}
              <div className="flex gap-2">
                <div className="flex-1 font-mono text-sm bg-muted p-2 rounded truncate">
                  {link.client_url}
                </div>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => copyToClipboard(link.client_url)}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                    <Eye className="h-3 w-3" />
                    Views
                  </div>
                  <div className="font-semibold">
                    {link.view_count}
                    {link.max_views > 0 && (
                      <span className="text-muted-foreground">/{link.max_views}</span>
                    )}
                  </div>
                </div>

                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                    <Clock className="h-3 w-3" />
                    Expires
                  </div>
                  <div className="font-semibold text-sm">
                    {link.time_remaining}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Last Access</div>
                  <div className="font-semibold text-sm">
                    {link.last_accessed 
                      ? formatDistanceToNow(new Date(link.last_accessed), { addSuffix: true })
                      : 'Never'
                    }
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Features</div>
                  <div className="flex justify-center gap-1">
                    {link.download_enabled && (
                      <Download className="h-3 w-3 text-green-600" title="Downloads Enabled" />
                    )}
                    {link.watermark_enabled && (
                      <Shield className="h-3 w-3 text-blue-600" title="Watermarked" />
                    )}
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(link.client_url)}
                  className="flex-1"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy Link
                </Button>
                <Button variant="outline" size="sm">
                  <Eye className="h-3 w-3 mr-1" />
                  Analytics
                </Button>
                {link.is_valid && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => revokeLink(link.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    Revoke
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}