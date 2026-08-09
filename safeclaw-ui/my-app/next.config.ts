import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    unoptimized: true,
  },
  // Playwright / agents often hit 127.0.0.1; allow HMR + assets
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    return [
      // Proxy API routes to FastAPI backend
      {
        source: '/api/chat/stream',
        destination: 'http://localhost:8000/chat/stream',
      },
      {
        source: '/api/skills',
        destination: 'http://localhost:8000/skills',
      },
      {
        source: '/api/sessions',
        destination: 'http://localhost:8000/sessions',
      },
      {
        source: '/api/sessions/:id',
        destination: 'http://localhost:8000/sessions/:id',
      },
      {
        source: '/api/memory',
        destination: 'http://localhost:8000/memory',
      },
      {
        source: '/api/memory/cleanup',
        destination: 'http://localhost:8000/memory/cleanup',
      },
      {
        source: '/api/system',
        destination: 'http://localhost:8000/system',
      },
      {
        source: '/api/safety',
        destination: 'http://localhost:8000/safety',
      },
      {
        source: '/api/settings/models',
        destination: 'http://localhost:8000/settings/models',
      },
      // Health check
      {
        source: '/api/health',
        destination: 'http://localhost:8000/health',
      },
      // File upload
      {
        source: '/api/upload',
        destination: 'http://localhost:8000/api/upload',
      },
      // PPT / workspace preview files
      {
        source: '/api/workspace-file',
        destination: 'http://localhost:8000/api/workspace-file',
      },
    ];
  },
};

export default nextConfig;
