function deployEnv(): "DEV" | "PROD" {
  const v = import.meta.env.VITE_DEPLOY_ENV;
  return v === "PROD" ? "PROD" : "DEV";
}

export function DeployEnvBadge() {
  const env = deployEnv();
  return (
    <span
      className={`badge deploy-env deploy-env-${env.toLowerCase()}`}
      title={`Dashboard deploy environment: ${env}`}
    >
      {env}
    </span>
  );
}
