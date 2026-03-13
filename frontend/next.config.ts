import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  basePath: "/memorials",
  output: "standalone",
};

export default nextConfig;
