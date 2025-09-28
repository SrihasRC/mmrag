/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    turbopack: {
      resolveAlias: {
        canvas: './empty-module.js',
      },
    },
  },
  webpack: (config, { isServer }) => {
    // Handle canvas module for react-pdf
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        canvas: false,
      }
    }

    return config
  },
}

module.exports = nextConfig
