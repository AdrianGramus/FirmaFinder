import { useState, useCallback, useEffect } from "react";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { t } from "../i18n";
import { MagnifyingGlass, FloppyDisk, Check, Globe, ArrowSquareOut, Buildings, FunnelSimple, CalendarBlank } from "@phosphor-icons/react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SearchPage() {
  const { language } = useLanguage();
  const { token } = useAuth();
  const [searchMode, setSearchMode] = useState("caen"); // "caen" or "name"
  const [query, setQuery] = useState("");
  const [county, setCounty] = useState("40");
  const [selectedCaens, setSelectedCaens] = useState([]);
  const [counties, setCounties] = useState([]);
  const [caenCodes, setCaenCodes] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savedCuis, setSavedCuis] = useState(new Set());
  const [sinceDate, setSinceDate] = useState("");
  const [caenDropdownOpen, setCaenDropdownOpen] = useState(false);

  useEffect(() => {
    axios.get(`${API}/counties`).then((r) => setCounties(r.data)).catch(() => {});
    axios.get(`${API}/caen-codes`).then((r) => setCaenCodes(r.data)).catch(() => {});
  }, []);

  // Close CAEN dropdown on outside click
  useEffect(() => {
    if (!caenDropdownOpen) return;
    const handleClick = (e) => {
      if (!e.target.closest('[data-testid="caen-select"]') && !e.target.closest('[data-testid="caen-dropdown"]')) {
        setCaenDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [caenDropdownOpen]);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const toggleCaen = (code) => {
    setSelectedCaens((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const toggleAll = () => {
    if (selectedCaens.length === caenCodes.length) {
      setSelectedCaens([]);
    } else {
      setSelectedCaens(caenCodes.map((c) => c.code));
    }
  };

  const doSearch = useCallback(async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      let res;
      const dateParam = sinceDate || undefined;
      if (searchMode === "caen" && selectedCaens.length > 0) {
        const codesParam = selectedCaens.join(",");
        res = await axios.get(`${API}/search/caen/${codesParam}`, {
          params: { county, since_date: dateParam },
          headers,
          withCredentials: true,
        });
      } else if (searchMode === "name" && query.trim()) {
        res = await axios.get(`${API}/search`, {
          params: { q: query.trim(), county, type: "name", since_date: dateParam },
          headers,
          withCredentials: true,
        });
      } else {
        toast.error(language === "ro" ? "Selecteaza cel putin un cod CAEN sau introdu un nume" : "Select at least one CAEN code or enter a name");
        setLoading(false);
        return;
      }
      setResults(res.data);
    } catch (err) {
      toast.error(language === "ro" ? "Eroare la cautare" : "Search error");
    } finally {
      setLoading(false);
    }
  }, [searchMode, selectedCaens, query, county, sinceDate, language, token, headers]);

  const handleSave = async (company) => {
    try {
      await axios.post(`${API}/companies`, {
        company_name: company.company_name,
        cui: company.cui,
        address: company.address || "",
        county: company.county || "",
        caen_code: company.caen_code || selectedCaens[0] || "",
        caen_description: company.caen_description || "",
        source_url: company.source_url || "",
        status: "potential_lead",
        establishment_date: company.establishment_date || "",
        phone: company.phone || "",
        j_number: company.j_number || "",
      }, { headers, withCredentials: true });
      setSavedCuis((prev) => new Set([...prev, company.cui]));
      toast.success(language === "ro" ? "Lead salvat!" : "Lead saved!");
    } catch (err) {
      const msg = err.response?.data?.detail || "Error";
      toast.error(msg);
    }
  };

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="search-page">
      <div>
        <h1 className="font-heading font-bold text-2xl sm:text-3xl text-[#0A0A0A] tracking-tight">
          {language === "ro" ? "Cauta Companii" : "Search Companies"}
        </h1>
        <p className="text-sm text-[#52525B] font-body mt-1">
          {language === "ro"
            ? "Date reale de la Ministerul Finantelor (mfinante.gov.ro)"
            : "Live data from Romanian Ministry of Finance (mfinante.gov.ro)"}
        </p>
      </div>

      {/* Search mode toggle */}
      <div className="flex gap-1 border border-[#E4E4E7] bg-white p-1 w-fit">
        <button
          data-testid="mode-caen"
          onClick={() => setSearchMode("caen")}
          className={`px-4 py-1.5 text-sm font-body transition-colors ${searchMode === "caen" ? "bg-[#002FA7] text-white" : "text-[#52525B] hover:bg-[#F4F4F5]"}`}
        >
          {language === "ro" ? "Cauta dupa cod CAEN" : "Search by CAEN code"}
        </button>
        <button
          data-testid="mode-name"
          onClick={() => setSearchMode("name")}
          className={`px-4 py-1.5 text-sm font-body transition-colors ${searchMode === "name" ? "bg-[#002FA7] text-white" : "text-[#52525B] hover:bg-[#F4F4F5]"}`}
        >
          {language === "ro" ? "Cauta dupa nume" : "Search by name"}
        </button>
      </div>

      <form onSubmit={doSearch} className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row gap-2">
          {/* County selector */}
          <div className="w-full sm:w-48">
            <Select value={county} onValueChange={setCounty}>
              <SelectTrigger data-testid="county-select" className="rounded-sm border-[#E4E4E7] h-10">
                <SelectValue placeholder={language === "ro" ? "Judet" : "County"} />
              </SelectTrigger>
              <SelectContent className="max-h-72">
                {counties.map((c) => (
                  <SelectItem key={c.code} value={c.code}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {searchMode === "caen" ? (
            <div className="flex-1 relative">
              <button
                type="button"
                data-testid="caen-select"
                onClick={() => setCaenDropdownOpen(!caenDropdownOpen)}
                className="w-full flex items-center justify-between rounded-sm border border-[#E4E4E7] h-10 px-3 bg-white text-sm font-body text-left"
              >
                <span className={selectedCaens.length ? "text-[#0A0A0A]" : "text-[#A1A1AA]"}>
                  {selectedCaens.length === 0
                    ? (language === "ro" ? "Selecteaza coduri CAEN" : "Select CAEN codes")
                    : selectedCaens.length === caenCodes.length
                      ? (language === "ro" ? "Toate codurile selectate" : "All codes selected")
                      : `${selectedCaens.length} ${language === "ro" ? "coduri selectate" : "codes selected"}`}
                </span>
                <svg className="h-4 w-4 text-[#52525B]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {caenDropdownOpen && (
                <div className="absolute z-50 mt-1 w-full bg-white border border-[#E4E4E7] shadow-lg max-h-64 overflow-y-auto" data-testid="caen-dropdown">
                  <label className="flex items-center gap-2 px-3 py-2 border-b border-[#E4E4E7] bg-[#F9F9FB] hover:bg-[#F4F4F5] cursor-pointer sticky top-0">
                    <input
                      type="checkbox"
                      data-testid="caen-select-all"
                      checked={selectedCaens.length === caenCodes.length && caenCodes.length > 0}
                      onChange={toggleAll}
                      className="w-4 h-4 rounded border-[#E4E4E7] text-[#002FA7] focus:ring-[#002FA7]"
                    />
                    <span className="text-sm font-medium text-[#0A0A0A]">
                      {language === "ro" ? "Selecteaza tot" : "Select All"}
                    </span>
                  </label>
                  {caenCodes.map((c) => (
                    <label key={c.code} className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#F4F4F5] cursor-pointer">
                      <input
                        type="checkbox"
                        data-testid={`caen-checkbox-${c.code}`}
                        checked={selectedCaens.includes(c.code)}
                        onChange={() => toggleCaen(c.code)}
                        className="w-4 h-4 rounded border-[#E4E4E7] text-[#002FA7] focus:ring-[#002FA7]"
                      />
                      <span className="font-mono font-medium text-sm text-[#0A0A0A]">{c.code}</span>
                      <span className="text-xs text-[#52525B] truncate">{language === "ro" ? c.description_ro : c.description_en}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <Input
              data-testid="search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={language === "ro" ? "Introdu numele companiei" : "Enter company name"}
              className="flex-1 rounded-sm border-[#E4E4E7] h-10 font-body"
            />
          )}

          <Button
            type="submit"
            data-testid="search-button"
            disabled={loading}
            className="bg-[#002FA7] text-white rounded-sm hover:bg-[#002078] h-10 px-6"
          >
            <MagnifyingGlass size={16} className="mr-1.5" />
            {loading ? (language === "ro" ? "Se cauta..." : "Searching...") : (language === "ro" ? "Cauta" : "Search")}
          </Button>
        </div>

        {/* Establishment date filter */}
        <div className="flex items-center gap-2 flex-wrap">
          <CalendarBlank size={16} className="text-[#52525B]" />
          <span className="text-xs text-[#52525B] font-body">
            {language === "ro" ? "Filtreaza dupa data infiintarii (de la):" : "Filter by establishment date (since):"}
          </span>
          <Input
            data-testid="since-date"
            type="date"
            value={sinceDate}
            onChange={(e) => setSinceDate(e.target.value)}
            className="w-44 rounded-sm border-[#E4E4E7] h-8 text-sm font-mono"
          />
          {sinceDate && (
            <button onClick={() => setSinceDate("")} className="text-xs text-[#E63946] hover:underline font-body">
              {language === "ro" ? "Sterge filtru" : "Clear filter"}
            </button>
          )}
        </div>
      </form>

      <div className="border border-[#E4E4E7] bg-[#EFF6FF] p-3 flex items-start gap-2">
        <FunnelSimple size={18} className="text-[#002FA7] flex-shrink-0 mt-0.5" />
        <p className="text-xs text-[#0A0A0A] font-body">
          {searchMode === "caen"
            ? (language === "ro"
                ? "Cautarea dupa cod CAEN foloseste cuvinte cheie specifice industriei pe mfinante.gov.ro. Datele de infiintare sunt preluate automat din baza ANAF."
                : "CAEN code search uses industry-specific keywords on mfinante.gov.ro. Establishment dates are automatically fetched from the ANAF database.")
            : (language === "ro"
                ? "Returneaza maxim 100 companii din judetul selectat. Datele de infiintare sunt preluate automat din baza ANAF."
                : "Returns up to 100 companies from the selected county. Establishment dates are automatically fetched from the ANAF database.")}
        </p>
      </div>

      {results && (
        <div className="space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <p className="text-sm text-[#52525B] font-body">
              <span className="font-mono font-bold text-[#0A0A0A]">{results.total || 0}</span>{" "}
              {language === "ro" ? "companii gasite" : "companies found"}
              {results.caen_description && (
                <span className="ml-2">
                  — <span className="font-mono text-[#002FA7]">{results.caen_code}</span> {results.caen_description}
                </span>
              )}
              {results.since_date && (
                <span className="ml-2 text-xs">
                  ({language === "ro" ? "infiintate din" : "established since"} <span className="font-mono">{results.since_date}</span>)
                </span>
              )}
            </p>
            <Badge className="bg-[#F0FDF4] text-[#22C55E] rounded-sm text-[10px]">
              <Globe size={12} className="mr-1" /> mfinante.gov.ro + ANAF
            </Badge>
          </div>

          <div className="border border-[#E4E4E7] bg-white">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#E4E4E7]">
                  <th className="text-left p-3 text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B]">
                    {language === "ro" ? "Nume Companie" : "Company Name"}
                  </th>
                  <th className="text-left p-3 text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B] hidden md:table-cell">CUI</th>
                  <th className="text-left p-3 text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B] hidden sm:table-cell">
                    {language === "ro" ? "Judet" : "County"}
                  </th>
                  <th className="text-left p-3 text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B] hidden lg:table-cell">
                    {language === "ro" ? "Data Infiintarii" : "Est. Date"}
                  </th>
                  <th className="text-right p-3 text-[10px] font-semibold tracking-[0.2em] uppercase text-[#52525B] w-36">
                    {language === "ro" ? "Actiuni" : "Actions"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {results.companies?.map((c, i) => (
                  <tr key={`${c.cui}-${i}`} className="border-b border-[#E4E4E7] hover:bg-[#F9F9FB] transition-colors">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 bg-[#F1F5F9] flex items-center justify-center rounded-sm flex-shrink-0">
                          <Buildings size={13} className="text-[#002FA7]" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-[#0A0A0A] font-body">{c.company_name}</p>
                          {c.phone && <p className="text-[11px] text-[#52525B] font-mono">{c.phone}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="p-3 hidden md:table-cell">
                      <span className="text-sm font-mono text-[#52525B]">{c.cui}</span>
                    </td>
                    <td className="p-3 hidden sm:table-cell">
                      <span className="text-xs text-[#52525B] font-body">{c.county}</span>
                    </td>
                    <td className="p-3 hidden lg:table-cell">
                      {c.establishment_date ? (
                        <span className="text-xs font-mono text-[#0A0A0A]" data-testid={`est-date-${c.cui}`}>{c.establishment_date}</span>
                      ) : (
                        <span className="text-xs text-[#A1A1AA]">—</span>
                      )}
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <a href={c.source_url} target="_blank" rel="noopener noreferrer"
                          className="p-1.5 hover:bg-[#F4F4F5] rounded-sm transition-colors"
                          title={language === "ro" ? "Vezi pe mfinante.gov.ro" : "View on mfinante.gov.ro"}>
                          <ArrowSquareOut size={14} className="text-[#52525B]" />
                        </a>
                        {savedCuis.has(c.cui) ? (
                          <Badge className="bg-[#F0FDF4] text-[#22C55E] rounded-sm">
                            <Check size={12} className="mr-1" /> {language === "ro" ? "Salvat" : "Saved"}
                          </Badge>
                        ) : (
                          <Button data-testid={`save-lead-${c.cui}`} size="sm" onClick={() => handleSave(c)}
                            className="bg-[#002FA7] text-white rounded-sm hover:bg-[#002078] h-7 text-xs px-2.5">
                            <FloppyDisk size={12} className="mr-1" /> {language === "ro" ? "Salveaza" : "Save"}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!results.companies || results.companies.length === 0) && (
              <div className="p-8 text-center">
                <p className="text-sm text-[#52525B] font-body">
                  {language === "ro" ? "Niciun rezultat gasit." : "No results found."}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
