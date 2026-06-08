#!/usr/bin/env bash
set -euo pipefail

cat << 'NODE_EOF' > /app/environment/cli/index.js
#!/usr/bin/env node
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { program } = require('commander');

program
  .requiredOption('-p, --profile <profileId>')
  .requiredOption('-d, --dir <targetDirectory>')
  .requiredOption('-u, --apiUrl <apiUrl>')
  .parse(process.argv);

const options = program.opts();
const { profile, dir, apiUrl } = options;

let maxGlobalRetention = 3650;
const globalConfigPath = '/tmp/mlflow/global-config.json';
if (fs.existsSync(globalConfigPath)) {
  try {
    const globalConfig = JSON.parse(fs.readFileSync(globalConfigPath, 'utf8'));
    if (typeof globalConfig.globalMaxRetention === 'number') {
      maxGlobalRetention = globalConfig.globalMaxRetention;
    }
  } catch (e) {
    // ignore
  }
}

async function run() {
  try {
    const policyRes = await axios.get(`${apiUrl}/api/policies/${profile}`);
    const policy = policyRes.data;

    const portsRes = await axios.get(`${apiUrl}/api/port-assignments`);
    const portAssignments = portsRes.data.portAssignments;

    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const artifactsDir = path.join(dir, 'artifacts');
    if (!fs.existsSync(artifactsDir)) {
      fs.mkdirSync(artifactsDir, { recursive: true });
    }

    const portData = portAssignments[profile];
    if (!portData) {
      throw new Error("Port assignment not found");
    }

    const port = portData.assignedPort;
    if (port < portData.portRange[0] || port > portData.portRange[1]) {
      throw new Error("Assigned port out of range");
    }

    const retentionDays = Math.min(policy.maxRetentionDays, maxGlobalRetention);

    const trackingUri = policy.allowSqlite ? `sqlite://${path.resolve(dir, 'mlflow.db')}` : `http://127.0.0.1:${port}`;

    let envContent = '';
    for (const [key, value] of Object.entries(policy.environmentVars || {})) {
      envContent += `export ${key}="${value}"\n`;
    }
    envContent += `export MLFLOW_TRACKING_URI="${trackingUri}"\n`;

    fs.writeFileSync(path.join(dir, 'mlflow-env.sh'), envContent);

    const systemdContent = `[Unit]
Description=MLflow Tracking Server (${profile})

[Service]
ExecStart=/usr/local/bin/mlflow server --port ${port} --default-artifact-root ${artifactsDir}
EnvironmentFile=${path.join(dir, 'mlflow-env.sh')}

[Install]
WantedBy=default.target
`;
    fs.writeFileSync(path.join(dir, 'mlflow-tracker.service'), systemdContent);

    const auditManifest = {
      profileId: profile,
      timestamp: new Date().toISOString(),
      port: port,
      retentionDays: retentionDays
    };
    fs.writeFileSync(path.join(dir, 'audit-manifest.json'), JSON.stringify(auditManifest, null, 2));

  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

run();
NODE_EOF

chmod +x /app/environment/cli/index.js
