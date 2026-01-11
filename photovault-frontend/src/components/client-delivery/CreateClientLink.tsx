'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Copy, QrCode, Share2, Clock, Eye, Download, Shield } from 'lucide-react';
import { toast } from 'sonner';

interface CreateClientLinkProps {
  albumId: number;
  albumName: string;
  onLinkCreated?: (linkData: any) => void;
}

export function CreateClientLink({ albumId, albumName, onLinkCreated }: CreateClientLinkProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [linkData, setLinkData] = useState<any>(null);
  const [config, setConfig] = useState({
    expiry_hours: 168, // 7 days
    max_views: 0, // Unlimited
    download_enabled: true,
    watermark_enabled: false,
    watermark_text: '',
    passcode: '',
  });

  const expiryOptions = [
    { value: 24, label: '1 Day' },
    { value: 72, label: '3 Days' },
    { value: 168, label: '1 Week' },
    { value: 336, label: '2 Weeks' },
    { value: 720, label: '1 Month' },
    { value: 2160, label: '3 Months' },
  ];

  const viewLimitOptions = [
    { value: 0, label: 'Unlimited' },
    { value: 10, label: '10 Views' },
    { value: 25, label: '25 Views' },
    { value: 50, label: '50 Views' },
    { value: 100, label: '100 Views' },
  ];

  const handleCreateLink = async () => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/shares/client/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          album_id: albumId,
          ...config,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setLinkData(data.client_link);
        onLinkCreated?.(data.client_link);
        toast.success('Client delivery link created successfully!');
      } else {
        toast.error(data.error?.message || 'Failed to create link');
      }
    } catch (error) {
      toast.error('Failed to create client link');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  if (linkData) {
    return (
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Client Delivery Link Created
          </CardTitle>
          <CardDescription>
            Share this secure link with your client for {albumName}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Link URL */}
          <div className="space-y-2">
            <Label>Client Link</Label>
            <div className="flex gap-2">
              <Input
                value={linkData.client_url}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(linkData.client_url)}
              >
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon">
                <QrCode className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Link Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Expires
              </Label>
              <p className="text-sm text-muted-foreground">
                {linkData.time_remaining}
              </p>
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Views
              </Label>
              <p className="text-sm text-muted-foreground">
                {linkData.views_remaining} remaining
              </p>
            </div>
          </div>

          {/* Settings Summary */}
          <div className="space-y-2">
            <Label>Link Settings</Label>
            <div className="flex flex-wrap gap-2">
              {linkData.settings.download_enabled && (
                <div className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-md text-xs">
                  <Download className="h-3 w-3" />
                  Downloads Enabled
                </div>
              )}
              {linkData.settings.watermark_enabled && (
                <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs">
                  <Shield className="h-3 w-3" />
                  Watermarked
                </div>
              )}
              {linkData.settings.passcode_protected && (
                <div className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 rounded-md text-xs">
                  <Shield className="h-3 w-3" />
                  Passcode Protected
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setLinkData(null)}
              className="flex-1"
            >
              Create Another Link
            </Button>
            <Button
              onClick={() => copyToClipboard(linkData.client_url)}
              className="flex-1"
            >
              Copy & Share
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Share2 className="h-5 w-5" />
          Create Client Delivery Link
        </CardTitle>
        <CardDescription>
          Create a secure, professional link to share {albumName} with your client
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Expiry Settings */}
        <div className="space-y-2">
          <Label>Link Expiry</Label>
          <Select
            value={config.expiry_hours.toString()}
            onValueChange={(value) => setConfig({ ...config, expiry_hours: parseInt(value) })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {expiryOptions.map((option) => (
                <SelectItem key={option.value} value={option.value.toString()}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* View Limits */}
        <div className="space-y-2">
          <Label>View Limit</Label>
          <Select
            value={config.max_views.toString()}
            onValueChange={(value) => setConfig({ ...config, max_views: parseInt(value) })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {viewLimitOptions.map((option) => (
                <SelectItem key={option.value} value={option.value.toString()}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Download Settings */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Allow Downloads</Label>
            <p className="text-sm text-muted-foreground">
              Let clients download high-resolution images
            </p>
          </div>
          <Switch
            checked={config.download_enabled}
            onCheckedChange={(checked) => setConfig({ ...config, download_enabled: checked })}
          />
        </div>

        {/* Watermark Settings */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Add Watermark</Label>
              <p className="text-sm text-muted-foreground">
                Protect your images with a watermark
              </p>
            </div>
            <Switch
              checked={config.watermark_enabled}
              onCheckedChange={(checked) => setConfig({ ...config, watermark_enabled: checked })}
            />
          </div>

          {config.watermark_enabled && (
            <div className="space-y-2">
              <Label>Watermark Text</Label>
              <Input
                placeholder="© Your Photography Studio"
                value={config.watermark_text}
                onChange={(e) => setConfig({ ...config, watermark_text: e.target.value })}
              />
            </div>
          )}
        </div>

        {/* Passcode Protection */}
        <div className="space-y-2">
          <Label>Passcode Protection (Optional)</Label>
          <Input
            type="password"
            placeholder="Enter optional passcode"
            value={config.passcode}
            onChange={(e) => setConfig({ ...config, passcode: e.target.value })}
          />
          <p className="text-sm text-muted-foreground">
            Add an extra layer of security with a passcode
          </p>
        </div>

        {/* Create Button */}
        <Button
          onClick={handleCreateLink}
          disabled={isLoading}
          className="w-full"
          size="lg"
        >
          {isLoading ? 'Creating Link...' : 'Create Client Delivery Link'}
        </Button>
      </CardContent>
    </Card>
  );
}