import { useCallback, useState } from "react";

import { AgentNameSlug } from "@/api";
import type { ConversationTarget } from "@/types/conversationTarget";
import { useConversation } from "./useConversation";

export function useAgentConversationPanel() {
  const { load, clear, data, loading, error } = useConversation();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [agentName, setAgentName] = useState<AgentNameSlug | null>(null);

  const close = useCallback(() => {
    setOpen(false);
    setAgentName(null);
    clear();
  }, [clear]);

  const openConversation = useCallback(
    (target: ConversationTarget, panelTitle: string) => {
      setTitle(panelTitle);
      setAgentName(
        target.kind === "run_agent" ? target.agentName : AgentNameSlug.surveyor,
      );
      setOpen(true);
      void load(target);
    },
    [load],
  );

  return {
    open,
    title,
    agentName,
    loading,
    error,
    data,
    openConversation,
    close,
  };
}
