type AuthState = {
  token: string | null;
};

const TOKEN_KEY = "photovault_token";
const TOKEN_UPDATE_KEY = "photovault_token_updated";

const mem: AuthState = {
  token: typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null,
};

// Listen for token updates from other tabs
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === TOKEN_KEY && e.newValue) {
      // Token updated in another tab
      mem.token = e.newValue;
    } else if (e.key === TOKEN_UPDATE_KEY) {
      // Token refresh happened in another tab, reload token
      mem.token = localStorage.getItem(TOKEN_KEY);
      // Trigger auth refresh in this tab
      window.dispatchEvent(new Event("token-refreshed"));
    }
  });
}

export const authStore = {
  getToken() {
    if (typeof window === "undefined") return null;
    // Always read from localStorage (source of truth)
    const token = localStorage.getItem(TOKEN_KEY);
    // Sync mem.token
    mem.token = token;
    return token;
  },
  setToken(token: string | null) {
    if (typeof window === "undefined") return;
    if (!token) {
      localStorage.removeItem(TOKEN_KEY);
    } else {
      localStorage.setItem(TOKEN_KEY, token);
      // Notify other tabs
      localStorage.setItem(TOKEN_UPDATE_KEY, Date.now().toString());
      localStorage.removeItem(TOKEN_UPDATE_KEY); // Trigger storage event
    }
    // Sync mem.token
    mem.token = token;

    // Notify current tab components (like AuthProvider)
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("token-refreshed"));
    }
  },
  clear() {
    this.setToken(null);
  },
};
