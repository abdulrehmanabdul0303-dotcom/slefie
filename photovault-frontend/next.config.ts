import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8999',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;
