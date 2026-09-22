import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './pages/Dashboard';
import CandidateDetail from './pages/CandidateDetail';
import SubmitDocuments from './pages/SubmitDocuments';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Header for HR pages */}
        <Routes>
          <Route
            path="/*"
            element={
              <>
                <header className="bg-white shadow-sm">
                  <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-sm">TQ</span>
                      </div>
                      <h1 className="text-xl font-bold text-gray-900">TraqCheck</h1>
                    </div>
                  </div>
                </header>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/candidates/:id" element={<CandidateDetail />} />
                </Routes>
              </>
            }
          />
          {/* Candidate Portal - No header */}
          <Route path="/submit/:token" element={<SubmitDocuments />} />
        </Routes>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#333',
              color: '#fff',
            },
            success: {
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </BrowserRouter>
  );
}

export default App;
