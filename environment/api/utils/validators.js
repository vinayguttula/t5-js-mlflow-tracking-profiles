exports.isValidProfileId = (id) => {
  return typeof id === 'string' && id.length > 0;
};
