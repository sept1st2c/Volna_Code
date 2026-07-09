"use client";

import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef } from "react";
import type { editor } from "monaco-editor";

export interface CodeEditorPanelProps {
  value: string;
  language: string;
  onChange: (value: string) => void;
  /** Disables editing, e.g. while a submission is in flight. */
  readOnly?: boolean;
}

/**
 * Thin wrapper around @monaco-editor/react's <Editor>. This module is loaded
 * exclusively through `next/dynamic({ ssr: false })` from the tutor session
 * page — Monaco touches `window`/`self` and cannot run during SSR.
 *
 * Kept intentionally small and controlled (value + onChange) so wiring real
 * code-submission-over-data-channel logic in later is additive, not a rewrite.
 */
export default function CodeEditorPanel({
  value,
  language,
  onChange,
  readOnly = false,
}: CodeEditorPanelProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  const handleMount: OnMount = (editorInstance) => {
    editorRef.current = editorInstance;
  };

  return (
    <Editor
      height="100%"
      language={language}
      value={value}
      theme="vs-dark"
      onMount={handleMount}
      onChange={(next) => onChange(next ?? "")}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 13,
        fontFamily: "var(--font-geist-mono, ui-monospace, monospace)",
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        padding: { top: 12 },
      }}
    />
  );
}
