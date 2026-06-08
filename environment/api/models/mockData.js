const policies = [
  {
    profileId: "dev-local",
    maxRetentionDays: 30,
    allowSqlite: true,
    requireAuth: false,
    environmentVars: {
      MLFLOW_TRACKING_INSECURE_TLS: "true"
    }
  },
  {
    profileId: "prod-secure",
    maxRetentionDays: 365,
    allowSqlite: false,
    requireAuth: true,
    environmentVars: {
      MLFLOW_TRACKING_INSECURE_TLS: "false"
    }
  },
  {
    profileId: "test-max-retention",
    maxRetentionDays: 5000,
    allowSqlite: true,
    requireAuth: false,
    environmentVars: {}
  },
  {
    profileId: "test-invalid-port",
    maxRetentionDays: 30,
    allowSqlite: true,
    requireAuth: false,
    environmentVars: {}
  }
];

const portAssignments = {
  "dev-local": {
    assignedPort: 5000,
    portRange: [5000, 5010]
  },
  "prod-secure": {
    assignedPort: 5443,
    portRange: [5443, 5443]
  },
  "test-max-retention": {
    assignedPort: 5001,
    portRange: [5000, 5010]
  },
  "test-invalid-port": {
    assignedPort: 8080,
    portRange: [5000, 5010]
  }
};

const filesystemRoots = {
  allowedRoots: [
    "/var/mlflow",
    "/opt/mlflow",
    "/tmp/mlflow-dev"
  ],
  defaultRoot: "/var/mlflow"
};

// Expose a push function so the verifier can dynamically inject profiles without the agent knowing
const injectProfile = (policy, portAssignment) => {
  policies.push(policy);
  portAssignments[policy.profileId] = portAssignment;
};

module.exports = {
  policies,
  portAssignments,
  filesystemRoots,
  injectProfile
};
