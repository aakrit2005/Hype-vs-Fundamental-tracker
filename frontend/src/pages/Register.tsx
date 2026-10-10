import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { register } from "../api/auth";
import { getErrorMessage } from "../api/client";

export function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    try {
      await register(email, password);

      setMessage("Account created.");
      navigate("/login");
    } catch (error) {
      setError(getErrorMessage(error));
    }
  }

  return (
    <div className="card auth-wrap">
      <h1>Register</h1>

      {error && <p className="error">{error}</p>}
      {message && <p className="notice">{message}</p>}

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
            minLength={8}
            required
          />
          <span className="field-hint">Minimum 8 characters.</span>
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "8px" }}>
          Register
        </button>
      </form>
    </div>
  );
}