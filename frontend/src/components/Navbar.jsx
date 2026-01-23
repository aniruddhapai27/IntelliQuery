import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";

const Navbar = ({ isAuthenticated, onLogout }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate("/");
    setIsMenuOpen(false);
  };

  return (
    <nav className="bg-black/95 backdrop-blur-sm border-b border-yellow-600/30 fixed w-full top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="w-10 h-10 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-lg flex items-center justify-center shadow-lg shadow-yellow-500/20 group-hover:shadow-yellow-500/40 transition-all duration-300">
              <span className="text-black font-bold text-xl">IQ</span>
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 bg-clip-text text-transparent">
              IntelliQuery
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              to="/"
              className="text-gray-300 hover:text-yellow-400 transition-colors duration-200 font-medium"
            >
              Home
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-gray-300 hover:text-yellow-400 transition-colors duration-200 font-medium"
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-6 py-2 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black font-semibold rounded-lg hover:from-yellow-500 hover:to-yellow-400 transition-all duration-300 shadow-lg shadow-yellow-600/30 hover:shadow-yellow-500/50"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-gray-300 hover:text-yellow-400 transition-colors duration-200 font-medium"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-6 py-2 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black font-semibold rounded-lg hover:from-yellow-500 hover:to-yellow-400 transition-all duration-300 shadow-lg shadow-yellow-600/30 hover:shadow-yellow-500/50"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden text-gray-300 hover:text-yellow-400 focus:outline-none"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              {isMenuOpen ? (
                <path d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden pb-4 space-y-3">
            <Link
              to="/"
              onClick={() => setIsMenuOpen(false)}
              className="block text-gray-300 hover:text-yellow-400 transition-colors duration-200 font-medium py-2"
            >
              Home
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  onClick={() => setIsMenuOpen(false)}
                  className="block text-gray-300 hover:text-yellow-400 transition-colors duration-200 font-medium py-2"
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-6 py-2 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black font-semibold rounded-lg hover:from-yellow-500 hover:to-yellow-400 transition-all duration-300"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={() => setIsMenuOpen(false)}
                  className="block text-gray-300 hover:text-yellow-400 transition-colors duration-200 font-medium py-2"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  onClick={() => setIsMenuOpen(false)}
                  className="block px-6 py-2 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black font-semibold rounded-lg hover:from-yellow-500 hover:to-yellow-400 transition-all duration-300 text-center"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
