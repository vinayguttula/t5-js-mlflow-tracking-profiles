const express = require('express');
const morgan = require('morgan');
const cors = require('cors');

const policiesRoute = require('./routes/policies');
const portAssignmentsRoute = require('./routes/portAssignments');
const filesystemRootsRoute = require('./routes/filesystemRoots');
const { injectProfile } = require('./models/mockData');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(morgan('dev'));
app.use(express.json());

app.use('/api/policies', policiesRoute);
app.use('/api/port-assignments', portAssignmentsRoute);
app.use('/api/filesystem-roots', filesystemRootsRoute);

app.post('/api/__test/inject', (req, res) => {
  if (process.env.VERIFIER_MODE !== '1') {
    return res.status(403).json({ error: 'forbidden' });
  }

  const { policy, portAssignment } = req.body;
  if (policy && portAssignment) {
    injectProfile(policy, portAssignment);
    res.status(200).json({ status: 'ok' });
  } else {
    res.status(400).json({ error: 'missing data' });
  }
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`MLflow Policy API running on port ${PORT}`);
});
