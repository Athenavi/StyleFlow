import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Force turbopack to use project root (fixes lockfile detection in home dir)
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
