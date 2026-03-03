import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Allow frontend to proxy API calls to FastAPI in dev via env var
  // In production, set NEXT_PUBLIC_API_URL to the backend URL
}

export default nextConfig
