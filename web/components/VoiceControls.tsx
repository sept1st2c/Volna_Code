"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { Room, RoomEvent } from "livekit-client";
import { createLiveKitToken } from "@/lib/api";

export interface VoiceControlsProps {
  /** Used to derive the LiveKit room name, e.g. the problem slug. */
  problemSlug: string;
}

type VoiceStatus = "idle" | "connecting" | "connected" | "error";

/**
 * Connect / mic controls for the live tutoring voice session.
 *
 * The token fetch (`POST /livekit/token`) and the livekit-client room
 * connection are both real: this component will genuinely try to join a
 * LiveKit room. What it can't do yet is talk to a tutor, because the LiveKit
 * Agent worker (the Python voice loop from PLAN.md) doesn't exist yet. So
 * once connected, it explicitly checks whether any remote participant
 * (the agent) is in the room and surfaces an honest "no tutor agent present"
 * state instead of pretending the tutoring loop is live.
 */
export default function VoiceControls({ problemSlug }: VoiceControlsProps) {
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [agentPresent, setAgentPresent] = useState(false);
  const [micEnabled, setMicEnabled] = useState(false);

  const roomRef = useRef<Room | null>(null);
  // useId (not Math.random) keeps this pure during render while still giving
  // each mounted session a unique, stable LiveKit participant identity.
  const reactId = useId();
  const identityRef = useRef<string>(`student-${reactId.replace(/[^a-zA-Z0-9]/g, "")}`);

  const refreshAgentPresence = useCallback((room: Room) => {
    setAgentPresent(room.remoteParticipants.size > 0);
  }, []);

  const handleConnect = useCallback(async () => {
    setStatus("connecting");
    setErrorMessage(null);

    let tokenResponse;
    try {
      tokenResponse = await createLiveKitToken({
        room: `tutor-${problemSlug}`,
        identity: identityRef.current,
      });
    } catch (err) {
      console.warn(
        "[voice] POST /livekit/token failed. Expected until the FastAPI backend is running.",
        err,
      );
      setStatus("error");
      setErrorMessage(
        "Could not reach the voice backend (POST /livekit/token). Start the FastAPI server, or " +
          "this is expected if it isn't running yet.",
      );
      return;
    }

    const room = new Room();
    roomRef.current = room;

    room.on(RoomEvent.ParticipantConnected, () => refreshAgentPresence(room));
    room.on(RoomEvent.ParticipantDisconnected, () => refreshAgentPresence(room));
    room.on(RoomEvent.Disconnected, () => {
      setStatus("idle");
      setAgentPresent(false);
      setMicEnabled(false);
    });

    try {
      await room.connect(tokenResponse.url, tokenResponse.token);
      refreshAgentPresence(room);
      setStatus("connected");
    } catch (err) {
      console.error("[voice] livekit-client room.connect() failed.", err);
      setStatus("error");
      setErrorMessage(
        "Got a token, but connecting to the LiveKit room failed. Check the LiveKit URL/credentials.",
      );
      roomRef.current = null;
    }
  }, [problemSlug, refreshAgentPresence]);

  const handleDisconnect = useCallback(async () => {
    await roomRef.current?.disconnect();
    roomRef.current = null;
    setStatus("idle");
    setAgentPresent(false);
    setMicEnabled(false);
  }, []);

  const handleToggleMic = useCallback(async () => {
    const room = roomRef.current;
    if (!room) return;
    try {
      const next = !micEnabled;
      await room.localParticipant.setMicrophoneEnabled(next);
      setMicEnabled(next);
    } catch (err) {
      console.error("[voice] Could not toggle microphone (permission denied?).", err);
    }
  }, [micEnabled]);

  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
    };
  }, []);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">Voice session</h2>

      <div className="flex items-center gap-2">
        {status === "connected" ? (
          <>
            <button
              type="button"
              onClick={handleToggleMic}
              className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                micEnabled
                  ? "bg-emerald-600 text-white hover:bg-emerald-700"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <MicIcon />
              {micEnabled ? "Mic on" : "Mic off"}
            </button>
            <button
              type="button"
              onClick={handleDisconnect}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Disconnect
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleConnect}
            disabled={status === "connecting"}
            className="inline-flex items-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          >
            <MicIcon />
            {status === "connecting" ? "Connecting..." : "Connect voice"}
          </button>
        )}
      </div>

      <div className="mt-3 text-xs leading-5">
        {status === "idle" && (
          <p className="text-slate-500 dark:text-slate-400">Not connected.</p>
        )}
        {status === "connecting" && (
          <p className="text-slate-500 dark:text-slate-400">Requesting a room token and joining...</p>
        )}
        {status === "error" && (
          <p className="rounded-md bg-rose-50 px-2 py-1.5 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            {errorMessage}
          </p>
        )}
        {status === "connected" && !agentPresent && (
          <p className="rounded-md bg-amber-50 px-2 py-1.5 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
            Connected to the LiveKit room, but not yet connected to the voice tutor backend: the
            LiveKit Agent worker isn&apos;t running, so no one is listening yet.
          </p>
        )}
        {status === "connected" && agentPresent && (
          <p className="rounded-md bg-emerald-50 px-2 py-1.5 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300">
            Connected, and a tutor agent is present in the room.
          </p>
        )}
      </div>
    </section>
  );
}

function MicIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-4 w-4">
      <path
        d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path
        d="M19 11a7 7 0 0 1-14 0M12 18v3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
