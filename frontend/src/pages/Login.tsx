import { useState } from "react";
import { loginUser } from "../services/authService";
import type { AuthRole, AuthUser, LoginPayload } from "../services/authService";

interface LoginProps {
  onLogin: (user: AuthUser, token: string) => void;
}

interface LoginFormState {
  name: string;
  email: string;
  password: string;
  role: AuthRole;
}

const roleOptions: Array<{ value: AuthRole; label: string }> = [
  { value: "manufacturer", label: "Manufacturer" },
  { value: "driver", label: "Driver" },
  { value: "retailer", label: "Retailer" },
];

export function Login({ onLogin }: LoginProps) {
  const [form, setForm] = useState<LoginFormState>({
    name: "",
    email: "",
    password: "",
    role: "manufacturer",
  });
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field: keyof LoginFormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const payload: LoginPayload = {
        name: form.name,
        email: form.email,
        role: form.role,
      };
      const response = await loginUser(payload);
      onLogin(response.user, response.access_token);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed. Please double-check your details and try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-on-surface font-body">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-12 lg:px-8">
        <div className="rounded-3xl border border-outline-variant/10 bg-surface-container-low p-8 shadow-sm">
          <div className="mb-8 space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.32em] text-secondary">Sign in</p>
            <h1 className="text-4xl font-bold text-on-surface">Supply Chain Management</h1>
            <p className="max-w-2xl text-sm leading-6 text-secondary">
              Select your role to open the matching dashboard for manufacturers, drivers, or retailers.
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-on-surface">Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(event) => handleChange("name", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-outline px-4 py-3 bg-background text-on-surface shadow-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="Your name"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-on-surface">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(event) => handleChange("email", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-outline px-4 py-3 bg-background text-on-surface shadow-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-on-surface">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(event) => handleChange("password", event.target.value)}
                className="mt-2 w-full rounded-2xl border border-outline px-4 py-3 bg-background text-on-surface shadow-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="Enter your password"
                required
              />
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-on-surface">Role</label>
                <select
                  value={form.role}
                  onChange={(event) => handleChange("role", event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-outline px-4 py-3 bg-background text-on-surface shadow-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                >
                  {roleOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {error ? (
              <div className="rounded-3xl border border-danger/20 bg-danger-container p-4 text-sm text-danger">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-primary px-6 py-4 text-base font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-primary/60"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// anything
