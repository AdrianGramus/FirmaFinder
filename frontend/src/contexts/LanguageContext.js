import { createContext, useContext, useState, useCallback } from "react";

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem("firma_lang") || "en";
  });

  const toggleLanguage = useCallback(() => {
    setLanguage((prev) => {
      const next = prev === "en" ? "ro" : "en";
      localStorage.setItem("firma_lang", next);
      return next;
    });
  }, []);

  const setLang = useCallback((lang) => {
    localStorage.setItem("firma_lang", lang);
    setLanguage(lang);
  }, []);

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, setLang }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
