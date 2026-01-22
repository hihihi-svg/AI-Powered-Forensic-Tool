import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import ModuleA from "./pages/ModuleA";
import ModuleB from "./pages/ModuleB";
import ModuleC from "./pages/ModuleC";
import ModuleD from "./pages/ModuleD";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/module-a" element={<ModuleA />} />
          <Route path="/module-b" element={<ModuleB />} />
          <Route path="/module-c" element={<ModuleC />} />
          <Route path="/module-d" element={<ModuleD />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
