import { describe, expect, it } from "vitest";

import { canApplyOrganization } from "../presentation/organizationPresentation";

describe("ClipOrganizationPanel apply guard", () => {
  it("does not enable apply after preview alone", () => {
    const preview = {
      applied: false,
      eligible: true,
      risk: "NONE",
      action: "MOVE",
      message: "Dry-run: no se movió el archivo.",
    };
    expect(canApplyOrganization(preview, { confirmed: false, busy: false })).toBe(false);
  });

  it("keeps apply disabled in the error/collision state", () => {
    expect(
      canApplyOrganization(
        { applied: false, eligible: false, risk: "COLLISION" },
        { confirmed: true, busy: false },
      ),
    ).toBe(false);
  });
});
