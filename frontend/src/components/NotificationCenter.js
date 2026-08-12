import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { t } from "../i18n";
import { Bell, CheckCircle, WarningCircle, Robot, X, EnvelopeSimple } from "@phosphor-icons/react";
import { ScrollArea } from "../components/ui/scroll-area";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function NotificationCenter() {
  const { language } = useLanguage();
  const { token } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/notifications`, { headers, withCredentials: true });
      setNotifications(res.data);
      setUnreadCount(res.data.filter((n) => !n.is_read).length);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  useEffect(() => {
    if (unreadCount > 0 && "Notification" in window && Notification.permission === "granted") {
      const newest = notifications.find((n) => !n.is_read);
      if (newest) {
        new Notification(newest.title, { body: newest.message, icon: "/favicon.ico" });
      }
    }
  }, [unreadCount, notifications]);

  const markRead = async (id) => {
    try {
      await axios.put(`${API}/notifications/${id}/read`, {}, { headers, withCredentials: true });
      fetchNotifications();
    } catch {
      // silent
    }
  };

  const markAllRead = async () => {
    try {
      await axios.put(`${API}/notifications/read-all`, {}, { headers, withCredentials: true });
      fetchNotifications();
    } catch {
      // silent
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case "email_sent":
        return <EnvelopeSimple size={16} className="text-[#22C55E]" />;
      case "ai_action":
        return <Robot size={16} className="text-[#002FA7]" />;
      case "overdue_reminder":
        return <WarningCircle size={16} className="text-[#E63946]" />;
      default:
        return <CheckCircle size={16} className="text-[#22C55E]" />;
    }
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h`;
    return `${Math.floor(hrs / 24)}d`;
  };

  return (
    <div className="relative">
      <button
        data-testid="notification-bell"
        onClick={() => {
          setOpen(!open);
          if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission();
          }
        }}
        className="relative p-2 hover:bg-[#F4F4F5] rounded-sm transition-colors"
      >
        <Bell size={20} weight={unreadCount > 0 ? "fill" : "regular"} className="text-[#0A0A0A]" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-[#E63946] text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-80 bg-white border border-[#E4E4E7] shadow-sm z-50 rounded-sm">
          <div className="flex items-center justify-between p-3 border-b border-[#E4E4E7]">
            <span className="text-xs font-semibold tracking-[0.2em] uppercase text-[#52525B]">
              {t("notifications.title", language)}
            </span>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  data-testid="mark-all-read"
                  onClick={markAllRead}
                  className="text-xs text-[#002FA7] hover:underline"
                >
                  {t("notifications.mark_all_read", language)}
                </button>
              )}
              <button onClick={() => setOpen(false)}>
                <X size={16} className="text-[#52525B]" />
              </button>
            </div>
          </div>
          <ScrollArea className="max-h-80">
            {notifications.length === 0 ? (
              <p className="p-4 text-sm text-[#52525B] text-center font-body">
                {t("notifications.no_notifications", language)}
              </p>
            ) : (
              notifications.slice(0, 20).map((n) => (
                <button
                  key={n.id}
                  data-testid={`notification-${n.id}`}
                  onClick={() => markRead(n.id)}
                  className={`w-full text-left p-3 border-b border-[#E4E4E7] hover:bg-[#F9F9FB] transition-colors ${
                    !n.is_read ? "bg-[#EFF6FF]" : ""
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {getIcon(n.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[#0A0A0A] truncate font-body">
                        {n.title}
                      </p>
                      <p className="text-xs text-[#52525B] mt-0.5 line-clamp-2 font-body">
                        {n.message}
                      </p>
                      <p className="text-[10px] text-[#52525B] mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
