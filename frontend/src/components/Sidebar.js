import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { t } from "../i18n";
import {
  MagnifyingGlass,
  ChartBar,
  FunnelSimple,
  CalendarCheck,
  SignOut,
  Translate,
  Buildings,
} from "@phosphor-icons/react";

const navItems = [
  { key: "dashboard", path: "/dashboard", icon: ChartBar },
  { key: "search", path: "/search", icon: MagnifyingGlass },
  { key: "pipeline", path: "/pipeline", icon: FunnelSimple },
  { key: "reminders", path: "/reminders", icon: CalendarCheck },
];

export default function Sidebar({ onClose }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();
  const { language, toggleLanguage } = useLanguage();

  const handleNav = (path) => {
    navigate(path);
    if (onClose) onClose();
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <aside
      className="w-[220px] h-full bg-white border-r border-[#E4E4E7] flex flex-col"
      data-testid="sidebar"
    >
      <div className="p-4 border-b border-[#E4E4E7]">
        <div className="flex items-center gap-2">
          <Buildings size={22} weight="bold" className="text-[#002FA7]" />
          <span className="font-heading font-bold text-lg text-[#0A0A0A] tracking-tight">
            FirmaFinder
          </span>
        </div>
        <p className="text-[10px] tracking-[0.2em] uppercase text-[#52525B] mt-1 font-body">
          CRM
        </p>
      </div>

      <nav className="flex-1 py-3">
        {navItems.map(({ key, path, icon: Icon }) => {
          const isActive = location.pathname.startsWith(path);
          return (
            <button
              key={key}
              data-testid={`nav-${key}`}
              onClick={() => handleNav(path)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-body transition-colors ${
                isActive
                  ? "bg-[#F1F5F9] text-[#002FA7] border-r-2 border-[#002FA7] font-medium"
                  : "text-[#52525B] hover:bg-[#F9F9FB] hover:text-[#0A0A0A]"
              }`}
            >
              <Icon size={18} weight={isActive ? "bold" : "regular"} />
              {t(`nav.${key}`, language)}
            </button>
          );
        })}
      </nav>

      <div className="border-t border-[#E4E4E7] p-3 space-y-1">
        <button
          data-testid="language-toggle"
          onClick={toggleLanguage}
          className="w-full flex items-center gap-3 px-3 py-2 text-sm font-body text-[#52525B] hover:bg-[#F9F9FB] rounded-sm transition-colors"
        >
          <Translate size={18} />
          {language === "en" ? "RO" : "EN"}
        </button>
        <button
          data-testid="logout-button"
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 text-sm font-body text-[#E63946] hover:bg-[#FEF2F2] rounded-sm transition-colors"
        >
          <SignOut size={18} />
          {t("nav.logout", language)}
        </button>
      </div>
    </aside>
  );
}
