// Mock auth middleware to pad file count
exports.mockAuth = (req, res, next) => {
  next();
};
