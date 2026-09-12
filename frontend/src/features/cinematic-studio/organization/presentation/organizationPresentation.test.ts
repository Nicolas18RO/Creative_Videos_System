import { describe, expect, it } from "vitest";

import type { OrganizeResultDto } from "../../types/studio";
import { canApplyOrganization, riskLabel } from "./organizationPresentation";

const ok: OrganizeResultDto = {
  applied: false,
  eligible: true,
  risk: "NONE",
  action: "MOVE",
  proposed_filename: "F_PROBLEM_BACK_PAIN_POSTURE_01.mp4",
};

describe("canApplyOrganization", () => {
  it("blocks apply during preview without confirmation", () => {
    expect(canApplyOrganization(ok, { confirmed: false, busy: false })).toBe(false);
  });

  it("allows apply only when eligible, confirmed and idle", () => {
    expect(canApplyOrganization(ok, { confirmed: true, busy: false })).toBe(true);
  });

  it("blocks apply on collision even if confirmed", () => {
    expect(
      canApplyOrganization({ ...ok, risk: "COLLISION", eligible: false }, { confirmed: true, busy: false }),
    ).toBe(false);
  });

  it("blocks apply while busy", () => {
    expect(canApplyOrganization(ok, { confirmed: true, busy: true })).toBe(false);
  });
});

describe("riskLabel", () => {
  it("labels collision for the warning state", () => {
    expect(riskLabel("COLLISION")).toMatch(/colisión/i);
  });
});
