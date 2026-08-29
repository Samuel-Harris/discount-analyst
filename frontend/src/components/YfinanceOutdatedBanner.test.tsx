import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { YfinanceOutdatedBanner } from "./YfinanceOutdatedBanner";

describe("YfinanceOutdatedBanner", () => {
  it("names the installed and latest versions", () => {
    render(
      <YfinanceOutdatedBanner installedVersion="1.6.0" latestVersion="1.7.0" />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "yfinance 1.6.0 is installed; 1.7.0 is available on PyPI",
    );
  });
});
