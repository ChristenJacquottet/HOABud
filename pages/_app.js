// pages/_app.js
// Custom App component to include global styles across all pages
import '../styles/globals.css';

function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />;
}

export default MyApp;