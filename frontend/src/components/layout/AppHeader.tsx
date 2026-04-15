import { DeployEnvBadge } from "../DeployEnvBadge";
import { UiStateText } from "../UiStateText";

export interface AppHeaderProps {
  listError: string | null;
  listLoading: boolean;
}

export function AppHeader({ listError, listLoading }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div>
        <h1>Discount Analyst</h1>
        <div className="subtitle">
          Local pipeline dashboard · grouped workflow runs
        </div>
      </div>
      <div className="app-header-actions">
        <DeployEnvBadge />
        {listError ? (
          <UiStateText tone="error" as="span" className="app-header-status">
            {listError}
          </UiStateText>
        ) : listLoading ? (
          <UiStateText tone="loading" as="span" className="app-header-status">
            Loading runs…
          </UiStateText>
        ) : null}
      </div>
    </header>
  );
}
