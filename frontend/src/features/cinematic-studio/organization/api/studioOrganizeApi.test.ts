import { afterEach, describe, expect, it, vi } from "vitest";

import { applyOrganize, buildOrganizeApplyRequest, buildOrganizePreviewRequest, previewOrganize } from "./studioOrganizeApi";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("organize request builders", () => {
  it("preview never sets apply true", () => {
    expect(buildOrganizePreviewRequest("clip-1")).toEqual({ clip_id: "clip-1", apply: false });
  });

  it("apply is explicit", () => {
    expect(buildOrganizeApplyRequest("clip-1")).toEqual({ clip_id: "clip-1", apply: true });
  });
});

describe("organize API", () => {
  it("preview posts apply false", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ applied: false, risk: "NONE", eligible: true }),
    });
    vi.stubGlobal("fetch", fetchMock);
    await previewOrganize("clip-1");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body.apply).toBe(false);
    expect(body.clip_id).toBe("clip-1");
  });

  it("maps 409 collision without throwing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ applied: false, risk: "COLLISION", eligible: false }),
      }),
    );
    const result = await applyOrganize("clip-1");
    expect(result.risk).toBe("COLLISION");
    expect(result.applied).toBe(false);
  });

  it("surfaces 404 as error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ detail: "clip_not_found: x" }),
      }),
    );
    await expect(previewOrganize("missing")).rejects.toThrow(/clip_not_found/);
  });
});
