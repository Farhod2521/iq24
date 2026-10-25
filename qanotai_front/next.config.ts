import type { NextConfig } from "next";

// FastAPI backend. The browser only ever talks to this Next.js server; /api/* is proxied through,
// so the session cookie is first-party and there's no CORS. Read at build time (Docker passes it as a build arg).
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8080";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
  experimental: {
    agentFeedback: true,
    // the proxy above cuts requests at 30 s by default; AI test generation can take a minute or two
    proxyTimeout: 300_000,
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
