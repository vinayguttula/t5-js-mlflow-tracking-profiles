const { policies } = require('../models/mockData');

exports.getPolicies = (req, res) => {
  res.json({ policies });
};

exports.getPolicyById = (req, res) => {
  const profileId = req.params.profileId;
  const policy = policies.find(p => p.profileId === profileId);
  
  if (policy) {
    res.json(policy);
  } else {
    res.status(404).json({ error: "Policy not found" });
  }
};
