import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
    ];
  },
  serverExternalPackages: [],
  experimental: {
    proxyTimeout: 120000,
  },
};

export default nextConfig;
