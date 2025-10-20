/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enables React's Strict Mode, which helps identify potential problems in an application.
  reactStrictMode: true,

  // Configuration for the next/image component.
  images: {
    // Defines a list of allowed remote image patterns. This is more secure than 'domains'.
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**', // Allows any path from this hostname
      },
      // You can add more patterns here for other image sources.
      // Example for a CMS like Contentful:
      // {
      //   protocol: 'https',
      //   hostname: 'images.ctfassets.net',
      // },
    ],
  },
};

export default nextConfig;