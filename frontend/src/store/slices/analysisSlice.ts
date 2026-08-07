import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Analysis, AnalysisResults, analysisApi } from "@/services/api";

interface AnalysisState {
  items: Analysis[];
  total: number;
  currentResults: AnalysisResults | null;
  liveProgress: Record<string, { progress: number; stage: string; message: string }>;
  loading: boolean;
  error: string | null;
}

const initialState: AnalysisState = {
  items: [],
  total: 0,
  currentResults: null,
  liveProgress: {},
  loading: false,
  error: null,
};

export const fetchAnalyses = createAsyncThunk("analysis/fetchAll", async () => {
  const resp = await analysisApi.list();
  return resp.data;
});

export const fetchAnalysisResults = createAsyncThunk("analysis/fetchResults", async (id: string) => {
  const resp = await analysisApi.results(id);
  return resp.data;
});

export const uploadDump = createAsyncThunk("analysis/upload", async (file: File) => {
  const resp = await analysisApi.upload(file);
  return resp.data;
});

const analysisSlice = createSlice({
  name: "analysis",
  initialState,
  reducers: {
    updateLiveProgress(
      state,
      action: PayloadAction<{ analysisId: string; progress: number; stage: string; message: string }>
    ) {
      const { analysisId, progress, stage, message } = action.payload;
      state.liveProgress[analysisId] = { progress, stage, message };
    },
    clearCurrentResults(state) {
      state.currentResults = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAnalyses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAnalyses.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchAnalyses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? "Failed to load analyses";
      })
      .addCase(fetchAnalysisResults.fulfilled, (state, action) => {
        state.currentResults = action.payload;
      })
      .addCase(uploadDump.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      });
  },
});

export const { updateLiveProgress, clearCurrentResults } = analysisSlice.actions;
export default analysisSlice.reducer;
