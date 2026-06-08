const express = require('express');
const router = express.Router();
const fsRootsController = require('../controllers/fsRootsController');

router.get('/', fsRootsController.getFilesystemRoots);

module.exports = router;
