import { UiStateText } from "@/components/UiStateText";

export interface YfinanceOutdatedBannerProps {
  installedVersion: string;
  latestVersion: string;
}

export function YfinanceOutdatedBanner({
  installedVersion,
  latestVersion,
}: YfinanceOutdatedBannerProps) {
  return (
    <div className="app-shell-alert" role="status">
      <UiStateText tone="warning" as="p">
        yfinance {installedVersion} is installed; {latestVersion} is available
        on PyPI. Yahoo Finance access is unreliable on a stale client. Run{" "}
        <code>uv lock --upgrade-package yfinance && uv sync</code> and restart
        the dashboard.
      </UiStateText>
    </div>
  );
}
