const express = require('express');
const router = express.Router();
const portsController = require('../controllers/portsController');

router.get('/', portsController.getPortAssignments);

module.exports = router;
