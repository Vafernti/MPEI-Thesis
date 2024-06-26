const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  const proxyUrl = process.env.REACT_APP_PROXY_URL;

  if (proxyUrl) {
    app.use(
      '/api', // Adjust this path to match your API endpoint
      createProxyMiddleware({
        target: proxyUrl,
        changeOrigin: true,
      })
    );
    app.use(
      '/static_files', // Adjust this path to match your API endpoint
      createProxyMiddleware({
        target: proxyUrl,
        changeOrigin: true,
      })
    );
    app.use(
      '/users_media', // Adjust this path to match your API endpoint
      createProxyMiddleware({
        target: proxyUrl,
        changeOrigin: true,
      })
    );
  }
};
