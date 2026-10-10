import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { getAlerts, markAlertRead } from "../api/alerts";
import { getErrorMessage, getToken } from "../api/client";
import type { Alert } from "../types";

export function Alerts() {
  const token = getToken();

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    getAlerts()
      .then(setAlerts)
      .catch((error) => setError(getErrorMessage(error)));
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  async function handleMarkRead(alert: Alert) {
    try {
      const updated = await markAlertRead(alert.id);

      setAlerts((current) =>
        current.map((item) => (item.id === updated.id ? updated : item))
      );
    } catch (error) {
      setMessage(getErrorMessage(error));
    }
  }

  return (
    <div>
      <h1>Alerts</h1>

      {error && <p className="error">{error}</p>}
      {message && <p className="error">{message}</p>}

      {alerts.length === 0 && <p>No alerts yet.</p>}

      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Symbol</th>
            <th>Message</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.id}>
              <td>{alert.date}</td>
              <td>{alert.symbol}</td>
              <td>{alert.message}</td>
              <td>{alert.is_read ? "Read" : "Unread"}</td>

              <td>
                {!alert.is_read && (
                  <button onClick={() => handleMarkRead(alert)}>
                    Mark Read
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}