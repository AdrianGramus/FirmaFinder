import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { Buildings, Translate, Phone, EnvelopeSimple, Lock, User } from "@phosphor-icons/react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LoginPage() {
  const { language, toggleLanguage } = useLanguage();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isRegister) {
        if (!email.trim()) {
          toast.error(language === "ro" ? "Email-ul este obligatoriu" : "Email is required");
          setLoading(false);
          return;
        }
        if (!password.trim() || password.length < 6) {
          toast.error(language === "ro" ? "Parola trebuie sa aiba minim 6 caractere" : "Password must be at least 6 characters");
          setLoading(false);
          return;
        }
        const res = await axios.post(`${API}/auth/register`, {
          email: email.trim(),
          phone: phone.trim(),
          password,
          name: name.trim() || undefined,
        }, { withCredentials: true });
        login(res.data);
        toast.success(language === "ro" ? "Cont creat!" : "Account created!");
        navigate("/dashboard", { replace: true });
      } else {
        const identifier = email.trim();
        if (!identifier) {
          toast.error(language === "ro" ? "Introdu email-ul sau numarul de telefon" : "Enter your email or phone number");
          setLoading(false);
          return;
        }
        const res = await axios.post(`${API}/auth/login`, {
          identifier,
          password,
        }, { withCredentials: true });
        login(res.data);
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Error";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative" style={{ background: "#F9F9FB" }} data-testid="login-page">
      <div className="absolute top-4 right-4 z-10">
        <button data-testid="login-language-toggle" onClick={toggleLanguage}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E4E4E7] rounded-sm text-sm font-body text-[#52525B] hover:bg-[#F4F4F5] transition-colors">
          <Translate size={16} />{language === "en" ? "RO" : "EN"}
        </button>
      </div>
      <div className="relative z-10 w-full max-w-sm mx-4">
        <div className="bg-white border border-[#E4E4E7] p-8">
          <div className="flex items-center gap-2.5 mb-6">
            <Buildings size={28} weight="bold" className="text-[#002FA7]" />
            <span className="font-heading font-bold text-2xl text-[#0A0A0A] tracking-tight">FirmaFinder</span>
          </div>
          <h1 className="font-heading font-bold text-xl text-[#0A0A0A] tracking-tight mb-1" data-testid="auth-title">
            {isRegister
              ? (language === "ro" ? "Creeaza cont" : "Create Account")
              : (language === "ro" ? "Conecteaza-te" : "Sign In")}
          </h1>
          <p className="text-sm text-[#52525B] font-body mb-6">
            {language === "ro" ? "CRM pentru Managementul Lead-urilor" : "Lead Management CRM"}
          </p>
          <form onSubmit={handleSubmit} className="space-y-3">
            {isRegister && (
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" />
                <Input data-testid="register-name" value={name} onChange={(e) => setName(e.target.value)}
                  placeholder={language === "ro" ? "Nume (optional)" : "Name (optional)"}
                  className="rounded-sm border-[#E4E4E7] h-10 font-body pl-9" />
              </div>
            )}
            <div className="relative">
              <EnvelopeSimple size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" />
              <Input data-testid="auth-email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder={isRegister
                  ? (language === "ro" ? "Email" : "Email")
                  : (language === "ro" ? "Email sau numar de telefon" : "Email or phone number")}
                className="rounded-sm border-[#E4E4E7] h-10 font-body pl-9" autoComplete="username" />
            </div>
            {isRegister && (
              <div className="relative">
                <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" />
                <Input data-testid="auth-phone" value={phone} onChange={(e) => setPhone(e.target.value)}
                  placeholder={language === "ro" ? "Numar de telefon (optional)" : "Phone number (optional)"}
                  className="rounded-sm border-[#E4E4E7] h-10 font-body pl-9" type="tel" />
              </div>
            )}
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" />
              <Input data-testid="auth-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder={language === "ro" ? "Parola" : "Password"}
                className="rounded-sm border-[#E4E4E7] h-10 font-body pl-9" autoComplete={isRegister ? "new-password" : "current-password"} />
            </div>
            <Button data-testid="auth-submit" type="submit" disabled={loading}
              className="w-full bg-[#002FA7] text-white rounded-sm hover:bg-[#002078] h-11 font-medium">
              {loading
                ? (language === "ro" ? "Se proceseaza..." : "Processing...")
                : isRegister
                  ? (language === "ro" ? "Creeaza cont" : "Create Account")
                  : (language === "ro" ? "Conecteaza-te" : "Sign In")}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button data-testid="auth-toggle" onClick={() => setIsRegister(!isRegister)}
              className="text-sm text-[#002FA7] hover:underline font-body">
              {isRegister
                ? (language === "ro" ? "Ai deja cont? Conecteaza-te" : "Already have an account? Sign In")
                : (language === "ro" ? "Nu ai cont? Creeaza unul" : "Don't have an account? Register")}
            </button>
          </div>
          <div className="mt-4 pt-3 border-t border-[#E4E4E7]">
            <p className="text-[10px] tracking-[0.15em] uppercase text-[#52525B] text-center font-body">
              Printing Industry Lead Management
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
