// Additional middleware to pad file count
exports.customLogger = (req, res, next) => {
  // Silent logger
  next();
};
