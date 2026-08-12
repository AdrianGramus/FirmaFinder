import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { t } from "../i18n";
import {
  Buildings,
  Target,
  Handshake,
  XCircle,
  WarningCircle,
  CalendarCheck,
  Phone,
  EnvelopeSimple,
  ChatText,
} from "@phosphor-icons/react";
import { Badge } from "../components/ui/badge";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STAT_CONFIG = [
  { key: "total_companies", labelKey: "dashboard.total_companies", icon: Buildings, color: "#0A0A0A", bg: "#F9F9FB" },
  { key: "potential_leads", labelKey: "dashboard.potential_leads", icon: Target, color: "#002FA7", bg: "#EFF6FF" },
  { key: "prospects", labelKey: "dashboard.prospects", icon: Handshake, color: "#EAB308", bg: "#FFFBEB" },
  { key: "clients", labelKey: "dashboard.clients", icon: Handshake, color: "#22C55E", bg: "#F0FDF4" },
  { key: "rejected", labelKey: "dashboard.rejected", icon: XCircle, color: "#E63946", bg: "#FEF2F2" },
];

export default function DashboardPage() {
  const { language } = useLanguage();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/dashboard/stats`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        withCredentials: true,
      });
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const reminderIcon = (type) => {
    switch (type) {
      case "call": return <Phone size={14} className="text-[#002FA7]" />;
      case "email": return <EnvelopeSimple size={14} className="text-[#22C55E]" />;
      default: return <ChatText size={14} className="text-[#EAB308]" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-[#002FA7] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="dashboard-page">
      <div>
        <h1 className="font-heading font-bold text-2xl sm:text-3xl text-[#0A0A0A] tracking-tight">
          {t("dashboard.title", language)}
        </h1>
        {user && (
          <p className="text-sm text-[#52525B] font-body mt-1">
            {language === "en" ? `Welcome back, ${user.name}` : `Bine ai revenit, ${user.name}`}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-px bg-[#E4E4E7] border border-[#E4E4E7]">
        {STAT_CONFIG.map(({ key, labelKey, icon: Icon, color, bg }) => (
          <div
            key={key}
            data-testid={`stat-${key}`}
            className="bg-white p-4 flex flex-col items-start"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 flex items-center justify-center rounded-sm" style={{ backgroundColor: bg }}>
                <Icon size={16} weight="bold" style={{ color }} />
              </div>
            </div>
            <span className="font-mono text-2xl font-bold text-[#0A0A0A]">
              {stats?.[key] ?? 0}
            </span>
            <span className="text-[10px] tracking-[0.15em] uppercase text-[#52525B] font-body mt-1">
              {t(labelKey, language)}
            </span>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-px bg-[#E4E4E7] border border-[#E4E4E7]">
        <div className="bg-white p-5">
          <div className="flex items-center gap-2 mb-4">
            <CalendarCheck size={18} weight="bold" className="text-[#002FA7]" />
            <h2 className="text-xs font-semibold tracking-[0.2em] uppercase text-[#52525B]">
              {t("dashboard.upcoming_reminders", language)}
            </h2>
            {stats?.overdue_reminders > 0 && (
              <Badge variant="destructive" className="ml-auto rounded-sm text-[10px]">
                <WarningCircle size={12} className="mr-1" />
                {stats.overdue_reminders} {t("dashboard.overdue", language)}
              </Badge>
            )}
          </div>
          {!stats?.upcoming_reminders?.length ? (
            <p className="text-sm text-[#52525B] font-body">{t("dashboard.no_reminders", language)}</p>
          ) : (
            <div className="space-y-1">
              {stats.upcoming_reminders.map((r) => (
                <button
                  key={r.id}
                  data-testid={`reminder-${r.id}`}
                  onClick={() => navigate("/reminders")}
                  className={`w-full text-left flex items-center gap-3 p-2.5 border border-[#E4E4E7] hover:bg-[#F9F9FB] transition-colors ${
                    r.is_overdue ? "border-l-2 border-l-[#E63946] bg-[#FEF2F2]" : ""
                  }`}
                >
                  {reminderIcon(r.reminder_type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[#0A0A0A] truncate font-body">
                      {r.company_name}
                    </p>
                    <p className="text-[11px] text-[#52525B] font-mono">
                      {new Date(r.due_date).toLocaleString(language === "ro" ? "ro-RO" : "en-US", {
                        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                      })}
                    </p>
                  </div>
                  {r.is_overdue && (
                    <WarningCircle size={16} className="text-[#E63946] flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white p-5">
          <h2 className="text-xs font-semibold tracking-[0.2em] uppercase text-[#52525B] mb-4">
            {t("dashboard.recent_leads", language)}
          </h2>
          {!stats?.recent_companies?.length ? (
            <p className="text-sm text-[#52525B] font-body">{t("dashboard.no_leads", language)}</p>
          ) : (
            <div className="space-y-1">
              {stats.recent_companies.map((c) => (
                <button
                  key={c.id}
                  data-testid={`recent-${c.id}`}
                  onClick={() => navigate(`/company/${c.id}`)}
                  className="w-full text-left flex items-center gap-3 p-2.5 border border-[#E4E4E7] hover:bg-[#F9F9FB] transition-colors"
                >
                  <div className="w-8 h-8 bg-[#F1F5F9] flex items-center justify-center rounded-sm">
                    <Buildings size={14} className="text-[#002FA7]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[#0A0A0A] truncate font-body">
                      {c.company_name}
                    </p>
                    <p className="text-[11px] text-[#52525B] font-mono">{c.cui || c.county}</p>
                  </div>
                  <StatusBadge status={c.status} language={language} />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status, language }) {
  const config = {
    potential_lead: { label: t("pipeline.potential_lead", language), cls: "bg-[#F1F5F9] text-[#52525B]" },
    prospect: { label: t("pipeline.prospect", language), cls: "bg-[#EFF6FF] text-[#002FA7]" },
    client: { label: t("pipeline.client", language), cls: "bg-[#F0FDF4] text-[#22C55E]" },
    rejected: { label: t("pipeline.rejected", language), cls: "bg-[#FEF2F2] text-[#E63946]" },
    urgent: { label: "URGENT", cls: "bg-[#E63946] text-white" },
  };
  const c = config[status] || config.potential_lead;
  return (
    <span className={`text-[10px] font-semibold tracking-[0.1em] uppercase px-2 py-0.5 rounded-sm ${c.cls}`}>
      {c.label}
    </span>
  );
}

export { StatusBadge };
