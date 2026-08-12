import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { t } from "../i18n";
import { Phone, EnvelopeSimple, ChatText, Check, Trash, WarningCircle, CalendarPlus } from "@phosphor-icons/react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Calendar } from "../components/ui/calendar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function RemindersPage() {
  const { language } = useLanguage();
  const { token } = useAuth();
  const navigate = useNavigate();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("upcoming");
  const [companies, setCompanies] = useState([]);
  const [newOpen, setNewOpen] = useState(false);
  const [newCompany, setNewCompany] = useState("");
  const [newCompanyName, setNewCompanyName] = useState("");
  const [newType, setNewType] = useState("call");
  const [newDate, setNewDate] = useState(null);
  const [newTime, setNewTime] = useState("10:00");
  const [newMsg, setNewMsg] = useState("");

  const fetchReminders = useCallback(async () => {
    try {
      const params = filter === "upcoming" ? { upcoming: true } : {};
      const res = await axios.get(`${API}/reminders`, { params, headers, withCredentials: true });
      setReminders(res.data);
    } catch {
      console.error("Failed to fetch reminders");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const fetchCompanies = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/companies`, { headers, withCredentials: true });
      setCompanies(res.data);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => { fetchReminders(); fetchCompanies(); }, [fetchReminders, fetchCompanies]);

  const complete = async (id) => {
    try {
      await axios.post(`${API}/reminders/${id}/complete`, {}, { headers, withCredentials: true });
      toast.success(language === "ro" ? "Finalizat!" : "Completed!");
      fetchReminders();
    } catch {
      toast.error("Error");
    }
  };

  const remove = async (id) => {
    if (!window.confirm(t("common.confirm_delete", language))) return;
    try {
      await axios.delete(`${API}/reminders/${id}`, { headers, withCredentials: true });
      fetchReminders();
    } catch {
      toast.error("Error");
    }
  };

  const createReminder = async () => {
    if (!newCompany || !newDate) return;
    const d = new Date(newDate);
    const [h, m] = newTime.split(":");
    d.setHours(parseInt(h), parseInt(m), 0, 0);
    try {
      await axios.post(`${API}/reminders`, {
        company_id: newCompany,
        company_name: newCompanyName,
        reminder_type: newType,
        due_date: d.toISOString(),
        message: newMsg,
      }, { headers, withCredentials: true });
      toast.success(language === "ro" ? "Memento creat!" : "Reminder created!");
      setNewOpen(false);
      setNewDate(null);
      setNewMsg("");
      fetchReminders();
    } catch {
      toast.error("Error");
    }
  };

  const typeIcon = (type) => {
    switch (type) {
      case "call": return <Phone size={16} weight="bold" className="text-[#002FA7]" />;
      case "email": return <EnvelopeSimple size={16} weight="bold" className="text-[#22C55E]" />;
      default: return <ChatText size={16} weight="bold" className="text-[#EAB308]" />;
    }
  };

  const formatDate = (d) =>
    new Date(d).toLocaleString(language === "ro" ? "ro-RO" : "en-US", {
      weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-[#002FA7] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="reminders-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-heading font-bold text-2xl sm:text-3xl text-[#0A0A0A] tracking-tight">
          {t("reminders.title", language)}
        </h1>
        <div className="flex items-center gap-2">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger data-testid="reminder-filter" className="w-36 rounded-sm border-[#E4E4E7] h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="upcoming">{t("reminders.upcoming", language)}</SelectItem>
              <SelectItem value="all">{t("reminders.all", language)}</SelectItem>
            </SelectContent>
          </Select>
          <Dialog open={newOpen} onOpenChange={setNewOpen}>
            <DialogTrigger asChild>
              <Button data-testid="new-reminder-button" className="bg-[#002FA7] text-white rounded-sm hover:bg-[#002078] h-9">
                <CalendarPlus size={16} className="mr-1.5" /> {t("reminders.new_reminder", language)}
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-sm">
              <DialogHeader>
                <DialogTitle className="font-heading">{t("reminders.new_reminder", language)}</DialogTitle>
              </DialogHeader>
              <div className="space-y-3">
                <Select
                  value={newCompany}
                  onValueChange={(v) => {
                    setNewCompany(v);
                    const c = companies.find((x) => x.id === v);
                    setNewCompanyName(c?.company_name || "");
                  }}
                >
                  <SelectTrigger className="rounded-sm border-[#E4E4E7]">
                    <SelectValue placeholder={t("reminders.company", language)} />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.company_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={newType} onValueChange={setNewType}>
                  <SelectTrigger className="rounded-sm border-[#E4E4E7]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="call">{t("reminders.type_call", language)}</SelectItem>
                    <SelectItem value="message">{t("reminders.type_message", language)}</SelectItem>
                    <SelectItem value="email">{t("reminders.type_email", language)}</SelectItem>
                  </SelectContent>
                </Select>
                <Calendar
                  mode="single"
                  selected={newDate}
                  onSelect={setNewDate}
                  className="rounded-sm border border-[#E4E4E7]"
                />
                <Input
                  type="time"
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="rounded-sm border-[#E4E4E7]"
                />
                <Textarea
                  value={newMsg}
                  onChange={(e) => setNewMsg(e.target.value)}
                  placeholder={t("reminders.message", language)}
                  className="rounded-sm border-[#E4E4E7] font-body"
                  rows={2}
                />
                <Button
                  data-testid="create-new-reminder-submit"
                  onClick={createReminder}
                  disabled={!newCompany || !newDate}
                  className="w-full bg-[#002FA7] text-white rounded-sm hover:bg-[#002078]"
                >
                  {t("common.save", language)}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {reminders.length === 0 ? (
        <div className="border border-[#E4E4E7] bg-white p-12 text-center">
          <p className="text-sm text-[#52525B] font-body">{t("reminders.no_reminders", language)}</p>
        </div>
      ) : (
        <div className="border border-[#E4E4E7] bg-white divide-y divide-[#E4E4E7]">
          {reminders.map((r) => (
            <div
              key={r.id}
              data-testid={`reminder-item-${r.id}`}
              className={`flex items-center gap-3 p-3 transition-colors ${
                r.is_overdue ? "bg-[#FEF2F2] border-l-2 border-l-[#E63946]" : r.is_completed ? "opacity-50" : "hover:bg-[#F9F9FB]"
              }`}
            >
              {typeIcon(r.reminder_type)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => navigate(`/company/${r.company_id}`)}
                    className="text-sm font-medium text-[#0A0A0A] hover:text-[#002FA7] truncate font-body"
                  >
                    {r.company_name}
                  </button>
                  {r.is_overdue && !r.is_completed && (
                    <Badge variant="destructive" className="rounded-sm text-[9px] px-1.5 py-0">
                      <WarningCircle size={10} className="mr-0.5" /> {t("reminders.overdue", language)}
                    </Badge>
                  )}
                  {r.is_completed && (
                    <Badge className="bg-[#F0FDF4] text-[#22C55E] rounded-sm text-[9px] px-1.5 py-0">
                      <Check size={10} className="mr-0.5" /> {t("reminders.completed", language)}
                    </Badge>
                  )}
                  {r.ai_action_taken && (
                    <Badge className="bg-[#EFF6FF] text-[#002FA7] rounded-sm text-[9px] px-1.5 py-0">AI</Badge>
                  )}
                </div>
                <p className="text-[11px] font-mono text-[#52525B] mt-0.5">{formatDate(r.due_date)}</p>
                {r.message && (
                  <p className="text-xs text-[#52525B] font-body mt-0.5 truncate">{r.message}</p>
                )}
              </div>
              <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                {!r.is_completed && (
                  <button
                    data-testid={`complete-reminder-${r.id}`}
                    onClick={() => complete(r.id)}
                    className="p-1.5 hover:bg-[#F0FDF4] rounded-sm transition-colors"
                    title={t("reminders.mark_complete", language)}
                  >
                    <Check size={16} className="text-[#22C55E]" />
                  </button>
                )}
                <button
                  data-testid={`delete-reminder-${r.id}`}
                  onClick={() => remove(r.id)}
                  className="p-1.5 hover:bg-[#FEF2F2] rounded-sm transition-colors"
                  title={t("reminders.delete", language)}
                >
                  <Trash size={16} className="text-[#E63946]" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
