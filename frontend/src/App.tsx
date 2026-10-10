import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { Alerts } from "./pages/Alerts";
import { BacktestResults } from "./pages/BacktestResults";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { SignalReport } from "./pages/SignalReport";
import { TickerDetail } from "./pages/TickerDetail";
import { Watchlist } from "./pages/Watchlist";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tickers/:id" element={<TickerDetail />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/backtests" element={<BacktestResults />} />
        <Route path="/signal-report" element={<SignalReport />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
    </Routes>
  );
}