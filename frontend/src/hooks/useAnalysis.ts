import { useDispatch, useSelector, TypedUseSelectorHook } from "react-redux";
import { useEffect } from "react";
import type { RootState, AppDispatch } from "@/store";
import { AnalysisSocket, ProgressMessage } from "@/services/websocket";
import { updateLiveProgress } from "@/store/slices/analysisSlice";

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

/**
 * Subscribes to live WebSocket progress updates for a given analysis
 * and pushes them into the Redux store.
 */
export function useAnalysisProgress(analysisId: string | undefined) {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!analysisId) return;

    const socket = new AnalysisSocket(analysisId, (msg: ProgressMessage) => {
      if (msg.type === "progress" && msg.progress !== undefined) {
        dispatch(
          updateLiveProgress({
            analysisId,
            progress: msg.progress,
            stage: msg.stage ?? "",
            message: msg.message ?? "",
          })
        );
      }
    });
    socket.connect();

    return () => socket.close();
  }, [analysisId, dispatch]);

  return useAppSelector((state) => (analysisId ? state.analysis.liveProgress[analysisId] : undefined));
}
