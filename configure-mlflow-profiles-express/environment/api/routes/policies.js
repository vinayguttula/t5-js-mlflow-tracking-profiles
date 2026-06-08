const express = require('express');
const router = express.Router();
const policiesController = require('../controllers/policiesController');

router.get('/', policiesController.getPolicies);
router.get('/:profileId', policiesController.getPolicyById);

module.exports = router;
