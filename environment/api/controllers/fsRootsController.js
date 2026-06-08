const { filesystemRoots } = require('../models/mockData');

exports.getFilesystemRoots = (req, res) => {
  res.json(filesystemRoots);
};
