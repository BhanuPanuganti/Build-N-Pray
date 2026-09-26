import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // Publishing an interview waits on the agent. The default proxy timeout drops that request.
    proxyTimeout: 180_000,
  },
  async rewrites() {
    const api = process.env.API_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
