import { useNavigate } from "react-router-dom";
import Button from "../components/Button";
import Card from "../components/Card";

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-72 h-72 bg-yellow-600/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-yellow-600/10 rounded-full blur-3xl"></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-yellow-400 via-yellow-500 to-yellow-600 bg-clip-text text-transparent leading-tight">
              Voice-Driven Analytics
              <br />
              <span className="text-4xl md:text-6xl">Made Simple</span>
            </h1>
            <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
              Query SQL, MongoDB, and spreadsheet datasets using natural
              language.
              <span className="text-yellow-400"> No code required.</span>
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={() => navigate("/register")}
                className="text-lg px-8 py-4"
              >
                Get Started Free
              </Button>
              <Button variant="ghost" className="text-lg">
                Watch Demo
              </Button>
            </div>
          </div>

          {/* Animated Background Elements */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-yellow-600/10 rounded-full blur-3xl animate-pulse"></div>
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-yellow-600/5 rounded-full blur-3xl"></div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-black to-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Powerful Features for Modern Analytics
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Everything you need to query and analyze your data using natural
              language
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature Cards */}
            <Card hover>
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-lg flex items-center justify-center mb-4 shadow-lg shadow-yellow-500/30">
                <svg
                  className="w-6 h-6 text-black"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4 8a9 9 0 110-18 9 9 0 010 18z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-yellow-400 mb-3">
                SQL Queries
              </h3>
              <p className="text-gray-400">
                Query your relational databases using natural language. No SQL
                knowledge required.
              </p>
            </Card>

            <Card hover>
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-600 to-yellow-400 rounded-lg flex items-center justify-center mb-4 shadow-lg shadow-yellow-500/30">
                <svg
                  className="w-6 h-6 text-black"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 0v10m0-10c0 2.21-3.582 4-8 4s-8-1.79-8-4m16 0v10"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                MongoDB Support
              </h3>
              <p className="text-gray-400">
                Query NoSQL databases using natural language. Access document
                stores with ease.
              </p>
            </Card>

            {/* Feature 3 */}
            <Card hover>
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-600 to-yellow-500 rounded-lg flex items-center justify-center mb-4 shadow-lg shadow-yellow-500/30">
                <svg
                  className="w-6 h-6 text-black"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Spreadsheet Analytics
              </h3>
              <p className="text-gray-400">
                Analyze CSV and Excel files with simple voice commands. No code
                required.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <Card className="bg-gradient-to-r from-yellow-600/20 to-yellow-500/20 border-yellow-500/50">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to Transform Your Data Analytics?
            </h2>
            <p className="text-gray-300 text-lg mb-8 max-w-2xl mx-auto">
              Join thousands of analysts and teams using IntelliQuery to make
              data-driven decisions faster.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button onClick={() => navigate("/register")}>
                Get Started Free
              </Button>
              <Button variant="ghost">View Documentation</Button>
            </div>
          </div>
        </Card>
      </section>

      {/* Stats Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent mb-2">
              10k+
            </div>
            <div className="text-gray-400">Active Users</div>
          </div>
          <div>
            <div className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent mb-2">
              1M+
            </div>
            <div className="text-gray-400">Queries Processed</div>
          </div>
          <div>
            <div className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent mb-2">
              99.9%
            </div>
            <div className="text-gray-400">Uptime</div>
          </div>
          <div>
            <div className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent mb-2">
              24/7
            </div>
            <div className="text-gray-400">Support</div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
