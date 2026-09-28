import type { NextConfig } from "next";

/**
 * 后端地址（构建时读取，可用 frontend/.env.local 覆盖）：
 * 浏览器侧统一使用同源地址，由 Next.js 反向代理到 Django：
 *   /api/*    → 后端 API（含接口文档 /api/v1/docs）
 *   /media/*  → 用户上传/生成的图片文件
 *   /static/* → Django admin 等静态资源
 *
 * 这样无论用户用 http://localhost:3000、http://192.168.x.x:3000 还是
 * https://your-domain.com 打开页面，都不需要改任何前端配置或重新构建。
 *
 * 注意 1：rewrites 默认在文件系统路由之后匹配（afterFiles），因此前端自己的
 *         /media（媒体库）与 /admin/settings（AI 配置）页面不会被代理覆盖。
 * 注意 2：Django 管理后台（/admin/）以尾斜杠路由为基准，而 Next.js 代理转发
 *         时会规范化尾斜杠，直接代理会形成 301 循环，因此后台不经此前端端口
 *         暴露，改用后端端口访问：http://<主机>:<后端端口>/admin/
 */
const backendOrigin = (
  process.env.STYLEFLOW_BACKEND_ORIGIN || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  // 本地/局域网运行使用 `next start`（见根目录 start.py），因此不启用
  // output: 'standalone'（该模式要求改写启动方式并额外拷贝 public/.next/static，
  // 主要服务于容器镜像；如将来需要容器化，可自行打开并改用 server.js 启动）。
  reactStrictMode: true,
  // Force turbopack to use project root (fixes lockfile detection in home dir)
  turbopack: {
    root: process.cwd(),
  },
  // 避免 Next.js 对尾斜杠做规范化（否则会与后端产生重定向来回）
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${backendOrigin}/api/:path*` },
      { source: "/media/:path*", destination: `${backendOrigin}/media/:path*` },
      { source: "/static/:path*", destination: `${backendOrigin}/static/:path*` },
    ];
  },
};

export default nextConfig;
