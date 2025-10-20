import { create } from "zustand";
import { userApi } from "@/lib/api-services";

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
  initialize: async () => {
    try {
      const profile = await userApi.getProfile();
      set({ user: profile, isAuthenticated: true, isLoading: false });
    } catch (err) {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
  login: async (credentials) => {
    const response = await userApi.login(credentials);
    set({ user: response.user, isAuthenticated: true });
    return response;
  },
  logout: async () => {
    await userApi.logout();
    set({ user: null, isAuthenticated: false });
  }
}));

export default useAuthStore;