import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { t } from "../i18n";
import {
  ArrowLeft,
  FloppyDisk,
  Trash,
  MagnifyingGlass,
  CalendarPlus,
  Robot,
  Spinner,
  ChatCircleText,
  EnvelopeSimple,
  WhatsappLogo,
} from "@phosphor-icons/react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Calendar } from "../components/ui/calendar";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const STATUSES = ["potential_lead", "prospect", "client", "rejected"];

export default function CompanyDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const { token } = useAuth();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reminderOpen, setReminderOpen] = useState(false);
  const [reminderDate, setReminderDate] = useState(null);
  const [reminderType, setReminderType] = useState("call");
  const [reminderMsg, setReminderMsg] = useState("");
  const [reminderTime, setReminderTime] = useState("10:00");
  const [aiOpen, setAiOpen] = useState(false);
  const [aiContext, setAiContext] = useState("");
  const [aiMessage, setAiMessage] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchCompany = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/companies/${id}`, { headers, withCredentials: true });
      setCompany(res.data);
    } catch {
      toast.error("Company not found");
      navigate("/pipeline");
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => { fetchCompany(); }, [fetchCompany]);

  const handleChange = (field, value) => {
    setCompany((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/companies/${id}`, company, { headers, withCredentials: true });
      toast.success(language === "ro" ? "Salvat!" : "Saved!");
    } catch {
      toast.error(language === "ro" ? "Eroare la salvare" : "Save error");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(t("common.confirm_delete", language))) return;
    try {
      await axios.delete(`${API}/companies/${id}`, { headers, withCredentials: true });
      toast.success(language === "ro" ? "Companie stearsa" : "Company deleted");
      navigate("/pipeline");
    } catch {
      toast.error("Delete error");
    }
  };

  const handleCreateReminder = async () => {
    if (!reminderDate) return;
    const d = new Date(reminderDate);
    const [h, m] = reminderTime.split(":");
    d.setHours(parseInt(h), parseInt(m), 0, 0);
    try {
      await axios.post(`${API}/reminders`, {
        company_id: id,
        company_name: company.company_name,
        reminder_type: reminderType,
        due_date: d.toISOString(),
        message: reminderMsg,
      }, { headers, withCredentials: true });
      toast.success(language === "ro" ? "Memento creat!" : "Reminder created!");
      setReminderOpen(false);
      setReminderDate(null);
      setReminderMsg("");
    } catch {
      toast.error("Error creating reminder");
    }
  };

  const handleAiCompose = async () => {
    setAiLoading(true);
    try {
      const res = await axios.post(`${API}/ai/compose-message`, {
        company_name: company.company_name,
        contact_person: company.contact_person,
        email: company.email,
        context: aiContext,
        language,
      }, { headers, withCredentials: true });
      setAiMessage(res.data.message);
    } catch (err) {
      toast.error(language === "ro" ? "Eroare AI" : "AI error");
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-[#002FA7] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!company) return null;

  const fields = [
    { key: "company_name", label: "company.company_name" },
    { key: "cui", label: "company.cui", mono: true },
    { key: "j_number", label: "company.j_number", mono: true },
    { key: "caen_code", label: "company.caen_code", mono: true },
    { key: "caen_description", label: "company.caen_description" },
    { key: "email", label: "company.email" },
    { key: "phone", label: "company.phone", mono: true },
    { key: "contact_person", label: "company.contact_person" },
    { key: "address", label: "company.address" },
    { key: "county", label: "company.county" },
    { key: "establishment_date", label: "company.establishment_year", mono: true },
    { key: "website", label: "company.website" },
  ];

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="company-detail-page">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} data-testid="back-button" className="p-1.5 hover:bg-[#F4F4F5] rounded-sm transition-colors">
          <ArrowLeft size={20} className="text-[#52525B]" />
        </button>
        <div className="flex-1">
          <h1 className="font-heading font-bold text-2xl text-[#0A0A0A] tracking-tight">
            {company.company_name}
          </h1>
          <p className="text-xs font-mono text-[#52525B]">CUI: {company.cui}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Select value={company.status} onValueChange={(v) => handleChange("status", v)}>
          <SelectTrigger data-testid="status-select" className="w-44 rounded-sm border-[#E4E4E7] h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>{t(`pipeline.${s}`, language)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {company.caen_code && (
          <Button
            data-testid="search-same-caen"
            variant="outline"
            size="sm"
            onClick={() => navigate(`/search?caen=${company.caen_code}`)}
            className="rounded-sm border-[#E4E4E7] h-9"
          >
            <MagnifyingGlass size={14} className="mr-1" /> {t("company.search_same_caen", language)}
          </Button>
        )}
        <Button
          data-testid="set-reminder-button"
          variant="outline"
          size="sm"
          onClick={() => setReminderOpen(true)}
          className="rounded-sm border-[#E4E4E7] h-9"
        >
          <CalendarPlus size={14} className="mr-1" /> {t("company.set_reminder", language)}
        </Button>
        <Button
          data-testid="ai-compose-button"
          variant="outline"
          size="sm"
          onClick={() => setAiOpen(true)}
          className="rounded-sm border-[#E4E4E7] h-9"
        >
          <Robot size={14} className="mr-1" /> {t("company.compose_message", language)}
        </Button>
        {company.phone && (
          <Button
            data-testid="whatsapp-button"
            variant="outline"
            size="sm"
            onClick={() => {
              let num = company.phone.replace(/[^0-9+]/g, "");
              // Convert Romanian local format to international
              if (num.startsWith("0") && !num.startsWith("00")) {
                num = "40" + num.slice(1);
              } else if (num.startsWith("+")) {
                num = num.slice(1);
              }
              window.open(`https://wa.me/${num}`, "_blank", "noopener");
            }}
            className="rounded-sm border-[#25D366] text-[#25D366] hover:bg-[#25D366]/10 h-9"
          >
            <WhatsappLogo size={16} weight="fill" className="mr-1" /> WhatsApp
          </Button>
        )}
        {company.phone && (
          <Button
            data-testid="sms-button"
            variant="outline"
            size="sm"
            onClick={() => { window.location.href = `sms:${company.phone}`; }}
            className="rounded-sm border-[#22C55E] text-[#22C55E] hover:bg-[#22C55E]/10 h-9"
          >
            <ChatCircleText size={16} weight="bold" className="mr-1" /> SMS
          </Button>
        )}
        {company.email && (
          <Button
            data-testid="email-button"
            variant="outline"
            size="sm"
            onClick={() => { window.location.href = `mailto:${company.email}`; }}
            className="rounded-sm border-[#002FA7] text-[#002FA7] hover:bg-[#002FA7]/10 h-9"
          >
            <EnvelopeSimple size={16} weight="bold" className="mr-1" /> Email
          </Button>
        )}
      </div>

      <Dialog open={reminderOpen} onOpenChange={setReminderOpen}>
        <DialogContent className="rounded-sm">
          <DialogHeader>
            <DialogTitle className="font-heading">{t("reminders.new_reminder", language)}</DialogTitle>
          </DialogHeader>
            <div className="space-y-3">
              <Select value={reminderType} onValueChange={setReminderType}>
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
                selected={reminderDate}
                onSelect={setReminderDate}
                className="rounded-sm border border-[#E4E4E7]"
              />
              <Input
                type="time"
                value={reminderTime}
                onChange={(e) => setReminderTime(e.target.value)}
                className="rounded-sm border-[#E4E4E7]"
              />
              <Textarea
                value={reminderMsg}
                onChange={(e) => setReminderMsg(e.target.value)}
                placeholder={t("reminders.message", language)}
                className="rounded-sm border-[#E4E4E7] font-body"
                rows={2}
              />
              <Button
                data-testid="create-reminder-submit"
                onClick={handleCreateReminder}
                className="w-full bg-[#002FA7] text-white rounded-sm hover:bg-[#002078]"
              >
                {t("common.save", language)}
              </Button>
            </div>
          </DialogContent>
      </Dialog>
      <Dialog open={aiOpen} onOpenChange={setAiOpen}>
        <DialogContent className="rounded-sm max-w-lg">
            <DialogHeader>
              <DialogTitle className="font-heading">{t("company.compose_message", language)}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <Textarea
                value={aiContext}
                onChange={(e) => setAiContext(e.target.value)}
                placeholder={language === "ro" ? "Context (ex: urmarire oferta, intalnire)" : "Context (e.g., follow-up on proposal, meeting request)"}
                className="rounded-sm border-[#E4E4E7] font-body"
                rows={2}
              />
              <Button
                data-testid="ai-generate-button"
                onClick={handleAiCompose}
                disabled={aiLoading}
                className="w-full bg-[#002FA7] text-white rounded-sm hover:bg-[#002078]"
              >
                {aiLoading ? <Spinner size={16} className="animate-spin mr-2" /> : <Robot size={16} className="mr-2" />}
                {aiLoading ? (language === "ro" ? "Se genereaza..." : "Generating...") : (language === "ro" ? "Genereaza mesaj" : "Generate Message")}
              </Button>
              {aiMessage && (
                <div className="border border-[#E4E4E7] p-3 bg-[#F9F9FB]">
                  <p className="text-xs font-semibold tracking-[0.2em] uppercase text-[#52525B] mb-2">Generated Message</p>
                  <p className="text-sm text-[#0A0A0A] font-body whitespace-pre-wrap">{aiMessage}</p>
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-2 rounded-sm text-xs"
                    onClick={() => {
                      navigator.clipboard.writeText(aiMessage);
                      toast.success("Copied!");
                    }}
                  >
                    Copy to clipboard
                  </Button>
                </div>
              )}
            </div>
          </DialogContent>
      </Dialog>

      <div className="grid lg:grid-cols-2 gap-px bg-[#E4E4E7] border border-[#E4E4E7]">
        {fields.map(({ key, label, mono }) => (
          <div key={key} className="bg-white p-3 flex flex-col gap-1">
            <label className="text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B]">
              {t(label, language)}
            </label>
            <Input
              data-testid={`field-${key}`}
              value={company[key] || ""}
              onChange={(e) => handleChange(key, e.target.value)}
              className={`rounded-sm border-[#E4E4E7] h-9 ${mono ? "font-mono" : "font-body"}`}
            />
          </div>
        ))}
      </div>

      <div className="border border-[#E4E4E7] bg-white p-3">
        <label className="text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B] mb-1 block">
          {t("company.notes", language)}
        </label>
        <Textarea
          data-testid="field-notes"
          value={company.notes || ""}
          onChange={(e) => handleChange("notes", e.target.value)}
          rows={3}
          className="rounded-sm border-[#E4E4E7] font-body"
        />
      </div>

      {company.source_url && (
        <div className="text-xs text-[#52525B] font-body">
          {t("company.source", language)}:{" "}
          <a href={company.source_url} target="_blank" rel="noopener noreferrer" className="text-[#002FA7] hover:underline">
            {company.source_url}
          </a>
        </div>
      )}

      <div className="flex items-center gap-3">
        <Button
          data-testid="save-company-button"
          onClick={handleSave}
          disabled={saving}
          className="bg-[#002FA7] text-white rounded-sm hover:bg-[#002078] px-6"
        >
          <FloppyDisk size={16} className="mr-1.5" />
          {saving ? t("common.loading", language) : t("company.save_changes", language)}
        </Button>
        <Button
          data-testid="delete-company-button"
          onClick={handleDelete}
          variant="outline"
          className="rounded-sm border-[#E63946] text-[#E63946] hover:bg-[#FEF2F2]"
        >
          <Trash size={16} className="mr-1.5" /> {t("company.delete", language)}
        </Button>
      </div>
    </div>
  );
}
