import { Link, NavLink, Outlet } from "react-router-dom";

import { clearToken, getToken } from "../api/client";

function BrandMark() {
  return (
    <span className="brand-mark">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="#ffffff"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="3 17 9 11 13 15 21 7" />
        <polyline points="14 7 21 7 21 14" />
      </svg>
    </span>
  );
}

export function Layout() {
  const token = getToken();

  return (
    <div>
      <nav className="nav">
        <div className="nav-inner">
          <Link to="/" className="brand">
            <BrandMark />
            Hype Tracker
          </Link>

          <div className="nav-links">
            <NavLink to="/" end>
              Dashboard
            </NavLink>
            <NavLink to="/signal-report">Signal Report</NavLink>
            <NavLink to="/backtests">Backtests</NavLink>
            <NavLink to="/watchlist">Watchlist</NavLink>
            <NavLink to="/alerts">Alerts</NavLink>
          </div>

          <div className="nav-actions">
            {token ? (
              <button
                className="btn btn-ghost"
                onClick={() => {
                  clearToken();
                  window.location.assign("/");
                }}
              >
                Log out
              </button>
            ) : (
              <>
                <Link className="btn btn-ghost" to="/login">
                  Login
                </Link>
                <Link className="btn btn-primary" to="/register">
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="page">
        <Outlet />
      </main>

      <footer className="site-footer">
        For educational research only. Not investment advice.
      </footer>
    </div>
  );
}