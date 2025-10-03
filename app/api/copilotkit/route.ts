import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  OpenAIAdapter,
  LangGraphAgent
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
 
// Configure OpenRouter via OpenAI adapter
const serviceAdapter = new OpenAIAdapter({
  api_key: process.env.OPENROUTER_API_KEY,
  baseURL: process.env.OPENROUTER_BASE_URL || "https://openrouter.ai/api/v1",
  model: process.env.OPENROUTER_MODEL || "google/gemini-2.5-pro",
});
 
const runtime = new CopilotRuntime({
  remoteEndpoints : [{
    url : process.env.NEXT_PUBLIC_LANGGRAPH_URL || "http://localhost:8000/copilotkit",
  }]
});
 
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
 
  return handleRequest(req);
};