import type { ChatMessage, SubmissionResult } from "./types";

/**
 * Frontend-side mirror of the real-time contract implemented by
 * `server/agent/worker.py` (see its module docstring, "Data-channel message
 * contract") and by the installed `livekit-agents` RoomIO
 * (`livekit/agents/voice/room_io/room_io.py` and `_output.py`). Kept in one
 * place so `VoiceControls` and the tutor session page don't each re-derive
 * these constants/shapes.
 *
 * ---- Code submission (frontend -> worker) ----
 * Sent reliably over the LiveKit data channel with the default (empty)
 * topic via `room.localParticipant.publishData(...)`.
 *
 * ---- Execution result (worker -> frontend) ----
 * Published back the same way; shape is a 1:1 match for `SubmissionResult`
 * in `web/lib/types.ts` (see worker.py's `_build_submission_result`).
 *
 * ---- Spoken narration + user transcript (worker -> frontend) ----
 * NOT delivered via the older `RoomEvent.TranscriptionReceived` /
 * `Transcription` data-packet path -- the installed `livekit-agents` (see
 * `voice/room_io/_output.py`, class `_ParticipantStreamTranscriptionOutput`)
 * publishes both the agent's own synthesized narration and the forwarded
 * user STT transcript as **text streams**
 * (`local_participant.stream_text(topic=TOPIC_TRANSCRIPTION, ...)`), which
 * on the JS client side only surface via
 * `room.registerTextStreamHandler(topic, handler)` -- confirmed by reading
 * `livekit-client`'s bundled source: `handleDataPacket` only routes the
 * legacy `packet.value.case === 'transcription'` proto field to
 * `RoomEvent.TranscriptionReceived`, while `streamHeader`/`streamChunk`/
 * `streamTrailer` packets (what `stream_text` actually sends) go through
 * `IncomingDataStreamManager` and are only observable via
 * `registerTextStreamHandler`.
 *
 * The Python side tags each text-stream write with a `sender_identity`
 * (`server/.venv/Lib/site-packages/livekit/agents/voice/room_io/room_io.py`,
 * `_init_task`: the agent's own output is tagged with
 * `room.local_participant.identity`, the forwarded user transcript is tagged
 * with the linked remote participant's identity), which the JS client
 * receives as `participantInfo.identity` on the registered handler -- so a
 * message's identity equal to our own `room.localParticipant.identity` means
 * "this is our own recognized speech being echoed back" (role "user"),
 * anything else is the tutor (role "tutor").
 */

export const CODE_SUBMIT_MESSAGE_TYPE = "code_submit" as const;
export const EXECUTION_RESULT_MESSAGE_TYPE = "execution_result" as const;

/**
 * Matches `TOPIC_TRANSCRIPTION` in
 * `server/.venv/Lib/site-packages/livekit/agents/types.py`.
 */
export const TRANSCRIPTION_TOPIC = "lk.transcription";

/**
 * Matches `ATTRIBUTE_TRANSCRIPTION_SEGMENT_ID` in the same module -- used to
 * group repeated deltas of the same spoken turn into one growing chat
 * message instead of appending a new one per chunk.
 */
export const TRANSCRIPTION_SEGMENT_ID_ATTRIBUTE = "lk.segment_id";

/** Builds the exact `code_submit` payload bytes the worker's data-channel
 * handler expects (see `_wire_data_channel` / `_on_data_received` in
 * worker.py, which does `json.loads(packet.data.decode("utf-8"))`). */
export function buildCodeSubmitPayload(code: string): Uint8Array<ArrayBuffer> {
  const json = JSON.stringify({ type: CODE_SUBMIT_MESSAGE_TYPE, code });
  return new TextEncoder().encode(json);
}

/**
 * Decodes a `RoomEvent.DataReceived` payload and returns a `SubmissionResult`
 * if (and only if) it's a well-formed `execution_result` message. Any other
 * type, or malformed/non-JSON data, yields `null` so the caller can ignore
 * it rather than throw (matches the worker's own "ignore unknown types"
 * behavior on its side of the same channel).
 */
export function parseExecutionResult(payload: Uint8Array): SubmissionResult | null {
  let message: unknown;
  try {
    message = JSON.parse(new TextDecoder().decode(payload));
  } catch {
    return null;
  }

  if (
    typeof message !== "object" ||
    message === null ||
    (message as { type?: unknown }).type !== EXECUTION_RESULT_MESSAGE_TYPE
  ) {
    return null;
  }

  // Deliberate 1:1 field match with SubmissionResult (see worker.py's
  // `_build_submission_result` docstring) -- no reshaping needed, just drop
  // the `type` discriminator.
  const { submittedAt, allPassed, cases } = message as SubmissionResult & { type: string };
  return { submittedAt, allPassed, cases };
}

/**
 * Inserts or updates (by segment id) a streamed transcript message. Text
 * streams from `livekit-agents` yield the cumulative text seen so far on
 * each iteration (see `TextStreamReader`'s async-iterator docs), so the same
 * `id` is reused to grow one bubble instead of appending duplicates.
 */
export function upsertTranscriptMessage(
  messages: ChatMessage[],
  id: string,
  role: ChatMessage["role"],
  text: string,
): ChatMessage[] {
  const timestamp = new Date().toLocaleTimeString();
  const idx = messages.findIndex((m) => m.id === id);
  if (idx === -1) {
    return [...messages, { id, role, text, timestamp }];
  }
  const next = messages.slice();
  next[idx] = { ...next[idx], text, timestamp };
  return next;
}
