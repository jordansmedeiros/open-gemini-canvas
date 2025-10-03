"use client"

import "@copilotkit/react-ui/styles.css";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLayout } from "./contexts/LayoutContext";
export default function GoogleDeepMindChatUI() {
  const router = useRouter();
  const { updateLayout } = useLayout();
  useEffect(() => {
    updateLayout({ agent: "master_legal_agent" });
    router.push("/post-generator");
  }, [router]);

  return (
    <></>
  )
}
