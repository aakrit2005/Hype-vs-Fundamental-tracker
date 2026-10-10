import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { login } from "../api/auth";
import { getErrorMessage, setToken } from "../api/client";

export function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    try {
      const response = await login(email, password);
      setToken(response.access_token);

      navigate("/watchlist");
    } catch (error) {
      setError(getErrorMessage(error));
    }
  }

  return (
    <div className="card auth-wrap">
      <h1>Login</h1>

      {error && <p className="error">{error}</p>}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>

        <div className="field">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "8px" }}>
          Login
        </button>
      </form>
    </div>
  );
}