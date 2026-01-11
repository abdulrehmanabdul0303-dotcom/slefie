'use client';

import { useState } from 'react';
import { Copy, Check, Share2, QrCode } from 'lucide-react';
import { Button, Modal, Input } from './ui';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageId?: string;
  imageName?: string;
  onGenerateLink?: (imageId: string) => Promise<string>;
  onGenerateQR?: (link: string) => Promise<string>;
}

export function ShareModal({
  isOpen,
  onClose,
  imageId = '',
  imageName = 'Image',
  onGenerateLink,
  onGenerateQR,
}: ShareModalProps): React.ReactNode {
  const [shareLink, setShareLink] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expiryDays, setExpiryDays] = useState('7');

  const handleGenerateLink = async () => {
    if (!onGenerateLink || !imageId) return;

    setIsLoading(true);
    try {
      const link = await onGenerateLink(imageId);
      setShareLink(link);

      // Generate QR code if handler is provided
      if (onGenerateQR) {
        const qr = await onGenerateQR(link);
        setQrCode(qr);
      }
    } catch (error) {
      console.error('Generate link failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Share "${imageName}"`}>
      <div className="space-y-4">
        {!shareLink ? (
          <>
            {/* Expiry selector */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Link expires in
              </label>
              <select
                value={expiryDays}
                onChange={(e) => setExpiryDays(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl glass text-white bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
              >
                <option value="1">1 day</option>
                <option value="7">7 days</option>
                <option value="30">30 days</option>
                <option value="365">1 year</option>
                <option value="0">Never</option>
              </select>
            </div>

            {/* Generate button */}
            <Button
              variant="primary"
              fullWidth
              onClick={handleGenerateLink}
              loading={isLoading}
              disabled={isLoading || !imageId}
            >
              <Share2 className="w-4 h-4 mr-2" />
              Generate Share Link
            </Button>
          </>
        ) : (
          <>
            {/* Share link display */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Share Link
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={shareLink}
                  readOnly
                  className="flex-1 px-4 py-2.5 rounded-xl glass text-white bg-white/10 border border-white/20 focus:outline-none"
                />
                <Button
                  variant={copied ? 'secondary' : 'primary'}
                  onClick={handleCopyLink}
                  title={copied ? 'Copied!' : 'Copy to clipboard'}
                >
                  {copied ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-white/50 mt-2">
                This link expires in {expiryDays} {expiryDays === '1' ? 'day' : 'days'}
              </p>
            </div>

            {/* QR Code display */}
            {qrCode && (
              <div>
                <label className="block text-sm font-medium text-white mb-2">QR Code</label>
                <div className="flex justify-center p-4 bg-white/5 rounded-xl border border-white/10">
                  <img src={qrCode} alt="QR Code" className="w-48 h-48" />
                </div>
                <a
                  href={qrCode}
                  download={`qr-${imageName}.png`}
                  className="text-sm text-blue-400 hover:text-blue-300 transition-colors mt-2 block text-center"
                >
                  Download QR Code
                </a>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-3">
              <Button
                variant="secondary"
                fullWidth
                onClick={() => {
                  setShareLink('');
                  setQrCode('');
                }}
              >
                Generate New Link
              </Button>
              <Button variant="primary" fullWidth onClick={onClose}>
                Done
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
