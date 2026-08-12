import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AuthCallback() {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const params = new URLSearchParams(hash.replace("#", ""));
    const sessionId = params.get("session_id");

    if (!sessionId) {
      navigate("/login", { replace: true });
      return;
    }

    (async () => {
      try {
        const res = await axios.post(
          `${API}/auth/session`,
          { session_id: sessionId },
          { withCredentials: true }
        );
        login(res.data);
        navigate("/dashboard", { replace: true, state: { user: res.data } });
      } catch (err) {
        console.error("Auth callback failed:", err);
        navigate("/login", { replace: true });
      }
    })();
  }, [navigate, login]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F9F9FB]">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-[#002FA7] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-[#52525B] font-body">Authenticating...</p>
      </div>
    </div>
  );
}
