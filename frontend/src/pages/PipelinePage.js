import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { t } from "../i18n";
import { Buildings, ArrowRight } from "@phosphor-icons/react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { StatusBadge } from "./DashboardPage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUSES = ["potential_lead", "prospect", "client", "rejected"];
const STATUS_BG = {
  potential_lead: "#F1F5F9",
  prospect: "#EFF6FF",
  client: "#F0FDF4",
  rejected: "#FEF2F2",
};

export default function PipelinePage() {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchCompanies = useCallback(async () => {
    try {
      const params = filter !== "all" ? { status: filter } : {};
      const res = await axios.get(`${API}/companies`, { params, headers, withCredentials: true });
      setCompanies(res.data);
    } catch (err) {
      console.error("Failed to fetch companies:", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const updateStatus = async (id, newStatus) => {
    try {
      await axios.put(`${API}/companies/${id}`, { status: newStatus }, { headers, withCredentials: true });
      fetchCompanies();
    } catch {
      // silent
    }
  };

  const grouped = {};
  STATUSES.forEach((s) => (grouped[s] = []));
  companies.forEach((c) => {
    const key = STATUSES.includes(c.status) ? c.status : "potential_lead";
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(c);
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-[#002FA7] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="pipeline-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-heading font-bold text-2xl sm:text-3xl text-[#0A0A0A] tracking-tight">
          {t("pipeline.title", language)}
        </h1>
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger data-testid="pipeline-filter" className="w-44 rounded-sm border-[#E4E4E7] h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("pipeline.all", language)}</SelectItem>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>{t(`pipeline.${s}`, language)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {filter === "all" ? (
        <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-px bg-[#E4E4E7] border border-[#E4E4E7]">
          {STATUSES.map((status) => (
            <div key={status} className="bg-white flex flex-col">
              <div className="p-3 border-b border-[#E4E4E7] flex items-center justify-between" style={{ backgroundColor: STATUS_BG[status] }}>
                <span className="text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B]">
                  {t(`pipeline.${status}`, language)}
                </span>
                <span className="font-mono text-sm font-bold text-[#0A0A0A]">{grouped[status]?.length || 0}</span>
              </div>
              <div className="flex-1 p-2 space-y-1.5 min-h-[200px]">
                {grouped[status]?.length === 0 ? (
                  <p className="text-xs text-[#52525B] font-body text-center py-8">
                    {t("pipeline.no_companies", language)}
                  </p>
                ) : (
                  grouped[status].map((c) => (
                    <CompanyCard
                      key={c.id}
                      company={c}
                      language={language}
                      onNavigate={() => navigate(`/company/${c.id}`)}
                      onStatusChange={(s) => updateStatus(c.id, s)}
                      currentStatus={status}
                    />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="border border-[#E4E4E7] bg-white">
          {companies.length === 0 ? (
            <p className="p-8 text-center text-sm text-[#52525B] font-body">
              {t("pipeline.no_companies", language)}
            </p>
          ) : (
            <div className="divide-y divide-[#E4E4E7]">
              {companies.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center gap-3 p-3 hover:bg-[#F9F9FB] cursor-pointer transition-colors"
                  onClick={() => navigate(`/company/${c.id}`)}
                  data-testid={`pipeline-company-${c.id}`}
                >
                  <div className="w-8 h-8 bg-[#F1F5F9] flex items-center justify-center rounded-sm flex-shrink-0">
                    <Buildings size={14} className="text-[#002FA7]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[#0A0A0A] truncate font-body">{c.company_name}</p>
                    <p className="text-xs text-[#52525B] font-mono">{c.cui || c.county || ""}</p>
                  </div>
                  <StatusBadge status={c.status} language={language} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CompanyCard({ company, language, onNavigate, onStatusChange, currentStatus }) {
  const otherStatuses = STATUSES.filter((s) => s !== currentStatus);

  return (
    <div
      data-testid={`pipeline-card-${company.id}`}
      className="border border-[#E4E4E7] bg-white p-2.5 hover:-translate-y-0.5 hover:shadow-sm transition-all cursor-pointer"
      onClick={onNavigate}
    >
      <p className="text-sm font-medium text-[#0A0A0A] truncate font-body">{company.company_name}</p>
      <p className="text-[11px] text-[#52525B] font-mono mt-0.5">{company.cui}</p>
      {company.county && (
        <p className="text-[11px] text-[#52525B] font-body mt-0.5">{company.county}</p>
      )}
      <div className="flex items-center gap-1 mt-2" onClick={(e) => e.stopPropagation()}>
        {otherStatuses.map((s) => (
          <button
            key={s}
            onClick={() => onStatusChange(s)}
            className="flex items-center gap-0.5 text-[9px] tracking-[0.1em] uppercase px-1.5 py-0.5 border border-[#E4E4E7] hover:bg-[#F4F4F5] transition-colors rounded-sm"
            title={`${t("pipeline.move_to", language)} ${t(`pipeline.${s}`, language)}`}
          >
            <ArrowRight size={8} /> {t(`pipeline.${s}`, language).substring(0, 8)}
          </button>
        ))}
      </div>
    </div>
  );
}
