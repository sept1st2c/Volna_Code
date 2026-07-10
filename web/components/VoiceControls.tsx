"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { RemoteTrack, Room, RoomEvent, Track } from "livekit-client";
import { createLiveKitToken } from "@/lib/api";

export interface VoiceControlsProps {
  /** Used to derive the LiveKit room name, e.g. the problem slug. */
  problemSlug: string;
  /**
   * Fired once `room.connect()` resolves, handing the live `Room` instance
   * up to the parent so sibling components (chat transcript, code
   * submission) can use the same data channel this component connected.
   */
  onConnected?: (room: Room) => void;
  /** Fired on disconnect (explicit or the room dropping on its own). */
  onDisconnected?: () => void;
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
export default function VoiceControls({
  problemSlug,
  onConnected,
  onDisconnected,
}: VoiceControlsProps) {
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [agentPresent, setAgentPresent] = useState(false);
  const [micEnabled, setMicEnabled] = useState(false);
  // Some browsers block audio autoplay even after a user-gesture-triggered
  // room.connect(); when that happens livekit-client sets
  // room.canPlaybackAudio = false and fires AudioPlaybackStatusChanged. We
  // surface a manual "tap to enable audio" fallback rather than silently
  // leaving the tutor's voice unplayable with no explanation.
  const [audioBlocked, setAudioBlocked] = useState(false);

  const roomRef = useRef<Room | null>(null);
  // Attached remote <audio> elements, tracked so they can be torn down on
  // unsubscribe/disconnect instead of leaking hidden DOM nodes.
  const audioElsRef = useRef<Map<string, HTMLMediaElement>>(new Map());
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
        // The LiveKit Agent worker's room-naming convention (server/agent/worker.py,
        // _resolve_problem_slug) falls back to treating the room NAME itself as the
        // problem slug when no room metadata is set -- so this must be the bare
        // slug, not a prefixed variant, or the worker can't resolve which problem
        // to tutor and silently defaults to "two-sum".
        room: problemSlug,
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
      audioElsRef.current.forEach((el) => el.remove());
      audioElsRef.current.clear();
      onDisconnected?.();
    });

    // Nothing in this app used @livekit/components-react's
    // <RoomAudioRenderer/> (nor manually attached tracks at all) -- the
    // tutor's synthesized voice was being subscribed to over WebRTC but
    // never rendered to an actual <audio> element, so no sound ever played
    // regardless of mic state. This is the actual playback path.
    room.on(RoomEvent.TrackSubscribed, (track: RemoteTrack) => {
      if (track.kind !== Track.Kind.Audio) return;
      const key = track.mediaStreamTrack.id;
      const el = track.attach();
      el.autoplay = true;
      el.style.display = "none";
      document.body.appendChild(el);
      audioElsRef.current.set(key, el);
    });
    room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
      if (track.kind !== Track.Kind.Audio) return;
      track.detach().forEach((el) => el.remove());
      audioElsRef.current.delete(track.mediaStreamTrack.id);
    });
    room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
      setAudioBlocked(!room.canPlaybackAudio);
    });

    try {
      await room.connect(tokenResponse.url, tokenResponse.token);
      refreshAgentPresence(room);
      setStatus("connected");
      onConnected?.(room);
      // Still inside the click handler's async continuation, so this
      // counts as the user gesture browsers require to unlock audio
      // playback. If it's blocked anyway, AudioPlaybackStatusChanged above
      // flips audioBlocked so the UI can offer a manual retry.
      await room.startAudio().catch(() => setAudioBlocked(true));
    } catch (err) {
      console.error("[voice] livekit-client room.connect() failed.", err);
      setStatus("error");
      setErrorMessage(
        "Got a token, but connecting to the LiveKit room failed. Check the LiveKit URL/credentials.",
      );
      roomRef.current = null;
    }
  }, [problemSlug, refreshAgentPresence, onConnected, onDisconnected]);

  const handleDisconnect = useCallback(async () => {
    await roomRef.current?.disconnect();
    roomRef.current = null;
    setStatus("idle");
    setAgentPresent(false);
    setMicEnabled(false);
    onDisconnected?.();
  }, [onDisconnected]);

  const handleEnableAudio = useCallback(async () => {
    const room = roomRef.current;
    if (!room) return;
    try {
      await room.startAudio();
      setAudioBlocked(!room.canPlaybackAudio);
    } catch (err) {
      console.error("[voice] room.startAudio() retry failed.", err);
    }
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
    <section className="rounded-lg border border-hairline bg-surface p-4">
      <h2 className="mb-3 text-sm font-semibold text-ink">Voice session</h2>

      <div className="flex items-center gap-2">
        {status === "connected" ? (
          <>
            <button
              type="button"
              onClick={handleToggleMic}
              className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                micEnabled
                  ? "bg-emerald-600 text-white hover:bg-emerald-500"
                  : "bg-surface-2 text-ink-tint hover:bg-surface-3"
              }`}
            >
              <MicIcon />
              {micEnabled ? "Mic on" : "Mic off"}
            </button>
            <button
              type="button"
              onClick={handleDisconnect}
              className="rounded-md border border-hairline-strong px-3 py-2 text-sm font-medium text-ink-tint hover:bg-surface-2"
            >
              Disconnect
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={handleConnect}
            disabled={status === "connecting"}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-on-primary hover:bg-primary-deep disabled:cursor-not-allowed disabled:opacity-60"
          >
            <MicIcon />
            {status === "connecting" ? "Connecting..." : "Connect voice"}
          </button>
        )}
      </div>

      <div className="mt-3 text-xs leading-5">
        {status === "idle" && (
          <p className="text-steel">Not connected.</p>
        )}
        {status === "connecting" && (
          <p className="text-steel">Requesting a room token and joining...</p>
        )}
        {status === "error" && (
          <p className="rounded-md bg-rose-500/10 px-2 py-1.5 text-rose-300">
            {errorMessage}
          </p>
        )}
        {status === "connected" && !agentPresent && (
          <p className="rounded-md bg-amber-500/10 px-2 py-1.5 text-amber-300">
            Connected to the LiveKit room, but not yet connected to the voice tutor backend: the
            LiveKit Agent worker isn&apos;t running, so no one is listening yet.
          </p>
        )}
        {status === "connected" && agentPresent && (
          <p className="rounded-md bg-emerald-500/10 px-2 py-1.5 text-emerald-300">
            Connected, and a tutor agent is present in the room.
          </p>
        )}
        {status === "connected" && audioBlocked && (
          <button
            type="button"
            onClick={handleEnableAudio}
            className="mt-2 w-full rounded-md bg-amber-500/10 px-2 py-1.5 text-left text-amber-300 hover:bg-amber-500/20"
          >
            Your browser is blocking the tutor&apos;s voice from playing automatically. Click here to
            enable audio.
          </button>
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
