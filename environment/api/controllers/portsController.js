const { portAssignments } = require('../models/mockData');

exports.getPortAssignments = (req, res) => {
  res.json({ portAssignments });
};
