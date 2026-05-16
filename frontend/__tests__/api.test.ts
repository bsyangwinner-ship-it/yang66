import { describe, expect, it } from "vitest";
import { parseAgentSseBlock } from "../src/lib/api";

describe("agent SSE parsing", () => {
  it("parses named events with JSON payloads", () => {
    const event = parseAgentSseBlock(
      'event: tool_call\ndata: {"tool_call":{"tool_name":"nutrition_calculator","input":{},"output":{"score":72},"status":"success","latency_ms":8}}\n\n'
    );

    expect(event?.type).toBe("tool_call");
    expect(event?.tool_call?.tool_name).toBe("nutrition_calculator");
    expect(event?.tool_call?.status).toBe("success");
  });

  it("ignores empty SSE blocks", () => {
    expect(parseAgentSseBlock("\n\n")).toBeNull();
  });
});
