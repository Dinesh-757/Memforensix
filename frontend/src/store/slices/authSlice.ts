import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { authApi } from "@/services/api";

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  role: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  isAuthenticated: !!localStorage.getItem("access_token"),
  username: localStorage.getItem("username"),
  role: localStorage.getItem("role"),
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  "auth/login",
  async ({ username, password }: { username: string; password: string }) => {
    const resp = await authApi.login(username, password);
    localStorage.setItem("access_token", resp.data.access_token);
    localStorage.setItem("refresh_token", resp.data.refresh_token);
    const me = await authApi.me();
    localStorage.setItem("username", me.data.username);
    localStorage.setItem("role", me.data.role);
    return me.data;
  }
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout(state) {
      localStorage.clear();
      state.isAuthenticated = false;
      state.username = null;
      state.role = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.username = action.payload.username;
        state.role = action.payload.role;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? "Login failed";
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
