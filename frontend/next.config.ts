import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pins the workspace root to this folder. Without this, Turbopack walks
  // up looking for lockfiles and can pick a wrong root if one exists
  // elsewhere on the machine (e.g. in a parent directory).
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
